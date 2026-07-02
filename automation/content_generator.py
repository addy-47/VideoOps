"""Content generation using Google Gemini API.

Generates scripts, titles, descriptions, image prompts, and video search queries
for YouTube Shorts automation. Replaced OpenAI with Google Gemini SDK.
"""
import os  # for environment variables here
import logging
import time  # for exponential backoff
import re  # for filtering instructional labels
import json  # for parsing JSON responses

from google import genai
from google.genai import types

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Gemini client
_gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if _gemini_api_key:
    _client = genai.Client(api_key=_gemini_api_key)
else:
    _client = None
    logger.error(
        "No Gemini API key found. Set GEMINI_API_KEY (or GOOGLE_API_KEY) in .env"
    )


def _extract_json(text):
    """Extract JSON from text, handling markdown code blocks and prefixes.

    Args:
        text (str): Raw response text that may contain JSON.

    Returns:
        str: Cleaned JSON string, or empty string if extraction fails.
    """
    if not text or not text.strip():
        return ""

    # Remove markdown code block fences
    text = re.sub(r'```(?:json)?\s*', '', text)
    text = text.strip()

    # Find the first '{' and last '}'
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]

    return ""


def _call_gemini(prompt, model, max_tokens=800, temperature=0.7,
                 response_json=False):
    """Make a Gemini API call with retries.

    Args:
        prompt (str): The prompt text to send.
        model (str): The Gemini model name.
        max_tokens (int): Maximum output tokens.
        temperature (float): Creativity (0.0-1.0).
        response_json (bool): Whether to request structured JSON output.

    Returns:
        str: The response text.

    Raises:
        RuntimeError: If the client is not initialised or all retries fail.
    """
    if _client is None:
        raise RuntimeError(
            "Gemini client not initialised. Set GEMINI_API_KEY in .env"
        )

    config = {
        "max_output_tokens": max_tokens,
        "temperature": temperature,
    }
    if response_json:
        config["response_mime_type"] = "application/json"

    response = _client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )
    text = response.text
    # When JSON was requested but response includes markdown/prefix wrapping,
    # try to extract the clean JSON portion
    if response_json and text:
        extracted = _extract_json(text)
        if extracted:
            text = extracted
    return text


def filter_instructional_labels(script):
    """Filter out instructional labels from the script.

    Args:
        script (str): The raw script from the LLM

    Returns:
        str: Cleaned script with instructional labels removed
    """
    # Filter out common instructional labels
    script = re.sub(r'(?i)(opening shot|hook|attention(-| )grabber|intro|introduction)[:.\s]+', '', script)
    script = re.sub(r'(?i)(call to action|cta|outro|conclusion)[:.\s]+', '', script)
    script = re.sub(r'(?i)(key points?|main points?|talking points?)[:.\s]+', '', script)

    # Remove timestamp indicators
    script = re.sub(r'\(\d+-\d+ seconds?\)', '', script)
    script = re.sub(r'\(\d+ sec(ond)?s?\)', '', script)

    # Move hashtags to the end
    hashtags = re.findall(r'(#\w+)', script)
    script = re.sub(r'#\w+', '', script)

    # Remove lines that are primarily instructional
    lines = script.split('\n')
    filtered_lines = []

    for line in lines:
        line = line.strip()
        # Skip empty lines
        if not line:
            continue

        # Skip lines that are purely instructional
        if re.search(r'(?i)^(section|part|step|hook|cta|intro|outro)[0-9\s]*[:.-]', line):
            continue

        # Skip numbered list items that are purely instructional
        if re.search(r'(?i)^[0-9]+\.\s+(intro|outro|hook|call to action)', line):
            continue

        # Skip lines that are likely comments to the video creator
        if re.search(r'(?i)(remember to|make sure|tip:|note:)', line):
            continue

        filtered_lines.append(line)

    # Join lines and clean up spacing
    filtered_script = ' '.join(filtered_lines)

    # Clean up spacing
    filtered_script = re.sub(r'\s+', ' ', filtered_script).strip()

    # Append hashtags at the end if requested
    if hashtags:
        hashtag_text = ' '.join(hashtags)
        # Don't append hashtags in the actual script, they should be in the video description only
        # filtered_script += f"\n\n{hashtag_text}"

    return filtered_script


def generate_batch_video_queries(texts: list[str], overall_topic="technology",
                                 model="gemini-2.5-flash-lite", retries=3):
    """Generate concise video search queries for a batch of script texts
    using Gemini API, returning results as a JSON object.

    Args:
        texts (list[str]): Text contents from script sections.
        overall_topic (str): General topic of the video for context.
        model (str): The Gemini model to use.
        retries (int): Number of retry attempts.

    Returns:
        dict: Mapping of index (int) to query string (str).
              Returns empty dict on failure after retries.
    """
    # Prepare the input text part of the prompt
    formatted_texts = ""
    for i, text in enumerate(texts):
        formatted_texts += f"--- Card {i} ---\n{text}\n\n"

    prompt = f"""You are an assistant that generates search queries for stock video websites (like Pexels, Pixabay).
Based on the following text sections from a video script about '{overall_topic}', generate a concise (2-4 words) search query for EACH section. Focus on the key visual elements or concepts mentioned in each specific section.

Input Script Sections:
{formatted_texts}
Instructions:
1. Analyze each "Card [index]" section independently.
2. For each card index, generate the most relevant 2-4 word search query.
3. Return ONLY a single JSON object mapping the card index (as an integer key) to its corresponding query string (as a string value).

Example Output Format:
{{"0": "abstract technology background", "1": "glowing data lines", "2": "future city animation"}}"""

    for attempt in range(retries):
        try:
            response_text = _call_gemini(
                prompt=prompt,
                model=model,
                max_tokens=len(texts) * 30 + 200,
                temperature=0.5,
                response_json=True,
            )

            try:
                query_dict_str_keys = json.loads(response_text)
                # Convert string keys to integers
                query_dict = {int(k): v for k, v in query_dict_str_keys.items()}

                # Basic validation
                if (len(query_dict) == len(texts)
                        and all(isinstance(k, int) and 0 <= k < len(texts)
                                for k in query_dict)):
                    logger.info(
                        f"Successfully generated batch video queries for {len(texts)} sections."
                    )
                    return query_dict
                else:
                    logger.warning(
                        f"Generated JSON keys do not match expected indices. "
                        f"Response: {response_text}"
                    )

            except json.JSONDecodeError as json_e:
                logger.error(
                    f"Failed to parse JSON response from Gemini: {json_e}. "
                    f"Response: {response_text}"
                )
            except Exception as parse_e:
                logger.error(
                    f"Error processing JSON response: {parse_e}. "
                    f"Response: {response_text}"
                )

        except Exception as e:
            logger.error(
                f"Gemini API error generating batch video queries "
                f"(attempt {attempt + 1}/{retries}): {str(e)}"
            )

        if attempt < retries - 1:
            logger.info(
                f"Retrying batch query generation ({attempt + 2}/{retries})..."
            )
            time.sleep(2 ** attempt)
        else:
            logger.error(
                f"Failed to generate batch video queries after {retries} attempts."
            )

    return {}


def generate_batch_image_prompts(texts: list[str], overall_topic="technology",
                                  model="gemini-2.5-flash-lite", retries=3):
    """Generate detailed image generation prompts for a batch of script texts
    using Gemini API, returning results as a JSON object.

    Args:
        texts (list[str]): Text contents from script sections.
        overall_topic (str): General topic of the video for context.
        model (str): The Gemini model to use.
        retries (int): Number of retry attempts.

    Returns:
        dict: Mapping of index (int) to prompt string (str).
              Returns empty dict on failure after retries.
    """
    # Prepare the input text part of the prompt
    formatted_texts = ""
    for i, text in enumerate(texts):
        formatted_texts += f"--- Card {i} ---\n{text}\n\n"

    prompt = f"""You are an assistant that generates high-quality image prompts for AI image generation models like Stable Diffusion.
Based on the following text sections from a video script about '{overall_topic}', create a detailed image prompt for EACH section.

Input Script Sections:
{formatted_texts}

Instructions:
1. Analyze each "Card [index]" section independently.
2. For each card, create a detailed image prompt (15-30 words) that:
   - Captures the main concept of that specific section
   - Includes clear visual elements and composition
   - Maintains a consistent style/theme across all prompts
   - DO NOT include any style descriptors (like digital art, photorealistic, etc.) as the style will be applied separately
   - Focus only on WHAT should be in the image, not HOW it should be rendered
3. Return ONLY a single JSON object mapping the card index (as an integer key) to its corresponding image prompt (as a string value).

Example Output Format:
{{"0": "futuristic digital interface with flowing data, glowing blue elements, dark background, high detail, modern tech aesthetic", "1": "AI neural network visualization, interconnected nodes with energy flowing between them, depth of field, dramatic lighting"}}"""

    for attempt in range(retries):
        try:
            response_text = _call_gemini(
                prompt=prompt,
                model=model,
                max_tokens=len(texts) * 60 + 300,
                temperature=0.7,
                response_json=True,
            )

            try:
                prompt_dict_str_keys = json.loads(response_text)
                # Convert string keys to integers
                prompt_dict = {int(k): v for k, v in prompt_dict_str_keys.items()}

                # Basic validation
                if (len(prompt_dict) == len(texts)
                        and all(isinstance(k, int) and 0 <= k < len(texts)
                                for k in prompt_dict)):
                    logger.info(
                        f"Successfully generated batch image prompts for {len(texts)} sections."
                    )
                    return prompt_dict
                else:
                    logger.warning(
                        f"Generated JSON keys do not match expected indices. "
                        f"Response: {response_text}"
                    )

            except json.JSONDecodeError as json_e:
                logger.error(
                    f"Failed to parse JSON response from Gemini: {json_e}. "
                    f"Response: {response_text}"
                )
            except Exception as parse_e:
                logger.error(
                    f"Error processing JSON response: {parse_e}. "
                    f"Response: {response_text}"
                )

        except Exception as e:
            logger.error(
                f"Gemini API error generating batch image prompts "
                f"(attempt {attempt + 1}/{retries}): {str(e)}"
            )

        if attempt < retries - 1:
            logger.info(
                f"Retrying batch image prompt generation ({attempt + 2}/{retries})..."
            )
            time.sleep(2 ** attempt)
        else:
            logger.error(
                f"Failed to generate batch image prompts after {retries} attempts."
            )

    return {}


def generate_comprehensive_content(topic, model="gemini-2.5-flash-lite",
                                    max_tokens=1600, retries=3):
    """Generate a comprehensive content package for a YouTube Short
    in a single API call.

    Args:
        topic (str): The topic or latest news to create content for.
        model (str): The Gemini model to use.
        max_tokens (int): Maximum tokens for the response.
        retries (int): Number of retry attempts.

    Returns:
        dict: Dictionary containing:
            - script: Full script text
            - title: Engaging title for the short
            - description: Full description with hashtags
            - thumbnail_hf_prompt: Detailed prompt for HF image generation
            - thumbnail_unsplash_query: Simple query for Unsplash search

    Raises:
        RuntimeError: If client not initialised.
        Exception: If all retries fail.
    """
    if _client is None:
        raise RuntimeError(
            "Gemini client not initialised. Set GEMINI_API_KEY in .env"
        )

    # Current date for relevance
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""Create a complete content package for a YouTube Short about this topic: "{topic}"
Date: {current_date}

Provide ALL the following elements in a single JSON response:

1. "script": A 25-second script (100-140 words) that:
   - Starts with an attention-grabbing opening (0-3 seconds)
   - Highlights 1-2 key points about the topic (4-22 seconds)
   - Ends with a clear call to action (23-25 seconds)
   - Uses short, concise sentences
   - DOES NOT include labels like "Hook:", "Intro:", etc.
   - Is written as plain text to be spoken

2. "title": A catchy, engaging title for the YouTube Short (40-60 characters)
   - Should grab attention and hint at valuable content
   - Include relevant keywords for search

3. "description": A compelling video description (100-200 characters)
   - Summarizes the content
   - Includes 3-4 relevant trending hashtags

4. "thumbnail_hf_prompt": A detailed image prompt for AI image generation (20-30 words)
   - Should represent the core visual concept for the thumbnail
   - Include specific visual elements, composition details
   - DO NOT include style descriptors (like "digital art", "photorealistic")
   - Focus on WHAT should be in the image, not HOW it should be rendered
   - Should make viewers want to click

5. "thumbnail_unsplash_query": A simple 2-4 word query for searching stock photos
   - Should capture the core visual concept for a fallback thumbnail
   - Use common terms that would yield good stock photo results

Format the response as a valid JSON object with these exact field names."""

    for attempt in range(retries):
        try:
            response_text = _call_gemini(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=0.7,
                response_json=True,
            )

            try:
                # Parse and validate the JSON response
                content_package = json.loads(response_text)

                # Check if all required fields are present
                required_fields = [
                    "script", "title", "description",
                    "thumbnail_hf_prompt", "thumbnail_unsplash_query"
                ]
                missing_fields = [
                    field for field in required_fields
                    if field not in content_package
                ]

                if missing_fields:
                    logger.warning(
                        f"JSON response missing required fields: {missing_fields}"
                    )
                    raise ValueError(
                        f"Missing required fields in response: {missing_fields}"
                    )

                # Clean the script text of any remaining instructional labels
                content_package["script"] = filter_instructional_labels(
                    content_package["script"]
                )

                logger.info("Successfully generated comprehensive content package:")
                logger.info(f"Title: {content_package['title']}")
                logger.info(
                    f"Script length: {len(content_package['script'].split())} words"
                )
                logger.info(
                    f"Thumbnail HF prompt: "
                    f"{content_package['thumbnail_hf_prompt'][:50]}..."
                )
                logger.info(
                    f"Thumbnail Unsplash query: "
                    f"{content_package['thumbnail_unsplash_query']}"
                )

                return content_package

            except json.JSONDecodeError as json_e:
                logger.error(
                    f"Failed to parse JSON response from Gemini: {json_e}"
                )
                logger.error(f"Raw response: {response_text}")
                if attempt == retries - 1:
                    raise
            except ValueError as ve:
                logger.error(f"Invalid response format: {str(ve)}")
                if attempt == retries - 1:
                    raise

        except Exception as e:
            logger.error(
                f"Gemini API error (attempt {attempt + 1}/{retries}): {str(e)}"
            )
            if attempt == retries - 1:
                raise Exception(
                    f"Failed to generate content package after "
                    f"{retries} attempts: {str(e)}"
                )

        # Exponential backoff before next retry
        wait_time = 2 ** attempt
        logger.info(
            f"Retrying in {wait_time} seconds "
            f"(attempt {attempt + 1}/{retries})..."
        )
        time.sleep(wait_time)

    raise Exception(
        f"Failed to generate comprehensive content package after "
        f"{retries} attempts"
    )
