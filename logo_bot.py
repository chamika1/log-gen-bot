import os
import telebot
import requests
import json
import logging
from typing import Optional
from io import BytesIO

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the bot with your token
BOT_TOKEN = '7597832602:AAEnlsKpWT2mF2YzVUfKHCza_FLRAobJhiI'
bot = telebot.TeleBot(BOT_TOKEN)

# API Configuration
GETIMG_API_URL = 'https://api.getimg.ai/v1/stable-diffusion-xl/text-to-image'
GETIMG_API_KEY = 'key-3XbWkFO34FVCQUnJQ6A3qr702Eu7DDR1dqoJOyhMHqhruEhs22KUzR7w631ZFiA5OFZIba7i44qDQEMpKxzegOUm83vCfILb'

headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {GETIMG_API_KEY}',
    'Content-Type': 'application/json',
    'User-Agent': 'okhttp/4.12.0',
}

# Default logo generation parameters
DEFAULT_PARAMS = {
    'height': 1024,
    'width': 1024,
    'model': 'realvis-xl-v4',
    'steps': 30,
    'seed': 0,
    'response_format': 'url',
    'negative_prompt': 'watermark,ugly'
}

# Add logo style options
LOGO_STYLES = {
    "minimalist": "minimalist, clean lines, simple shapes, negative space, elegant",
    "modern": "modern, sleek, professional, corporate, bold typography",
    "vintage": "vintage, retro, classic, nostalgic, hand-drawn feel",
    "tech": "technology, digital, futuristic, innovative, geometric",
    "creative": "creative, artistic, colorful, playful, unique",
    "luxury": "luxury, premium, elegant, sophisticated, high-end"
}

# Remove the LOGO_STYLES dictionary

def download_image(url: str) -> Optional[bytes]:
    """Download image from URL and return bytes"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download image: {e}")
        return None

def generate_logo_image(prompt: str) -> Optional[str]:
    """Generate logo from prompt using GetImg AI API"""
    try:
        enhanced_prompt = f"professional high-quality logo design, {prompt}, modern corporate style, vector art, clean design, high contrast, centered composition, white background"
        logger.info(f"Generating logo with prompt: {enhanced_prompt}")
        
        json_data = {
            **DEFAULT_PARAMS,
            'prompt': enhanced_prompt
        }
        
        logger.info("Sending request to GetImg AI API...")
        response = requests.post(
            GETIMG_API_URL,
            headers=headers,
            json=json_data,
            timeout=30
        )
        response.raise_for_status()
        logger.info("Successfully received response from API")
        
        data = response.json()
        image_url = data.get('url')
        if image_url:
            logger.info(f"Generated image URL: {image_url}")
        else:
            logger.error("No image URL in response")
        return image_url
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse API response: {e}")
        return None

# Add at the top with other imports
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Add owner contact info
OWNER_USERNAME = "your_username"  # Replace with your Telegram username

def create_welcome_keyboard():
    """Create welcome message inline keyboard"""
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("📝 Generate Logo", callback_data="generate_logo"),
        InlineKeyboardButton("📞 Contact Owner", url=f"https://t.me/{OWNER_USERNAME}")
    )
    keyboard.row(
        InlineKeyboardButton("❓ Help", callback_data="help"),
    )
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
🎨 *Welcome to the Professional Logo Generator*

Create stunning, professional logos for your brand with advanced AI technology.

*What I can do:*
• Generate unique, high-quality logos
• Create modern and professional designs
• Provide various style options

*How to start:*
Use the buttons below or type /logo followed by your description.

_Example: /logo Create a modern tech company logo with blue gradient_
    """
    bot.reply_to(
        message,
        welcome_text,
        parse_mode='Markdown',
        reply_markup=create_welcome_keyboard()
    )

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
🔍 *Professional Logo Generator Help*

*Commands:*
• `/logo` - Generate a custom logo
• `/help` - Show this help message
• `/start` - Start the bot

*How to Generate a Logo:*
1. Use the `/logo` command followed by your description
2. Wait while our AI creates your logo
3. Receive your professional logo

*Example:*
`/logo Create a modern tech company logo with blue colors`

*Tips for Best Results:*
• Be specific about colors and style
• Mention the industry or business type
• Describe any specific symbols or elements

*Need Support?*
Contact our support team using the button in /start menu
    """
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "generate_logo":
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            "🎨 Please use the /logo command followed by your logo description.\n\n"
            "Example: `/logo Create a modern tech company logo with blue colors`",
            parse_mode='Markdown'
        )
    elif call.data == "help":
        bot.answer_callback_query(call.id)
        send_help(call.message)

@bot.message_handler(commands=['logo'])
def handle_logo_command(message):
    """Handle /logo command"""
    # Extract the text after the /logo command
    prompt = message.text.replace('/logo', '').strip()
    
    if not prompt:
        bot.reply_to(
            message,
            "⚠️ Please provide a description after the /logo command.\n"
            "Example: `/logo Create a modern tech company logo with blue colors`",
            parse_mode='Markdown'
        )
        return
        
    try:
        logger.info(f"Received logo request from user {message.from_user.id}: {prompt}")
        processing_msg = bot.reply_to(message, """🎨 Crafting Your Professional Logo...

Our AI is meticulously designing your unique brand identity.
Please allow a moment for perfection.""")
        
        # Generate logo
        logger.info("Starting logo generation...")
        image_url = generate_logo_image(prompt)
        if not image_url:
            logger.error("Failed to generate logo")
            bot.edit_message_text(
                "⚠️ Sorry, I couldn't generate the logo. Please try again.",
                chat_id=message.chat.id,
                message_id=processing_msg.message_id
            )
            return

        # Download image
        logger.info("Downloading generated image...")
        image_data = download_image(image_url)
        if not image_data:
            logger.error("Failed to download image")
            bot.edit_message_text(
                "⚠️ Sorry, I couldn't download the generated logo. Please try again.",
                chat_id=message.chat.id,
                message_id=processing_msg.message_id
            )
            return
            
        # Send the logo
        logger.info("Sending logo to user...")
        bot.send_photo(
            message.chat.id,
            photo=BytesIO(image_data),
            caption="""✨ Your Professional Logo is Ready!

Thank you for choosing our AI Logo Generator. We've crafted your unique design with precision and creativity.

Need refinements? Simply use /logo command with a new description to create another variation.

#ProfessionalLogo #AIDesign #BrandIdentity"""
        )
        logger.info("Logo sent successfully")
        
        # Delete the processing message
        bot.delete_message(message.chat.id, processing_msg.message_id)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        bot.edit_message_text(
            "⚠️ Sorry, something went wrong. Please try again.",
            chat_id=message.chat.id,
            message_id=processing_msg.message_id
        )

# Remove or modify the general message handler to ignore non-command messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Handle non-command messages"""
    if not message.text.startswith('/'):
        bot.reply_to(
            message,
            "⚠️ Please use the /logo command to generate logos.\n"
            "Example: `/logo Create a modern tech company logo`",
            parse_mode='Markdown'
        )
        return
        
    # Rest of the handle_message function remains the same...

@bot.message_handler(commands=['styles'])
def show_styles(message):
    styles_text = "Available logo styles:\n\n"
    for style, description in LOGO_STYLES.items():
        styles_text += f"• {style.capitalize()}: {description}\n"
    bot.reply_to(message, styles_text)

if __name__ == "__main__":
    logger.info("Starting the bot...")
    bot.polling(none_stop=True)