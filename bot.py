import requests
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Hardcoded API Keys and URLs
MOBILE_LOOKUP_URL = "https://tracexdata-api.onrender.com/api/lookup?key=vansh-30&query={}"
VEHICLE_LOOKUP_URL = "https://techvishalboss.com/api/v1/lookup.php?key=TVB_SGL_15A5F652&service=vehicle&rc={}"

# Bot Token (Replace with your actual bot token)
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when /start is issued."""
    keyboard = [
        [InlineKeyboardButton("🔍 Search Mobile Number", callback_data='search_mobile')],
        [InlineKeyboardButton("🚗 Search Vehicle Number", callback_data='search_vehicle')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🚀 *Welcome to Lookup Bot!*\n\n"
        "I can help you lookup information for:\n"
        "• 📱 Mobile Numbers (10 digits)\n"
        "• 🚗 Vehicle Numbers (Indian format)\n\n"
        "Select an option below or directly send me a number!"
    )
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'search_mobile':
        await query.edit_message_text(
            "📱 Please send me a 10-digit mobile number.\n\n"
            "Example: 8585696996\n"
            "You can also send with +91 (I'll remove it automatically)."
        )
        context.user_data['search_type'] = 'mobile'
    
    elif query.data == 'search_vehicle':
        await query.edit_message_text(
            "🚗 Please send me a vehicle registration number.\n\n"
            "Example: MH01AB1234\n"
            "Format: State code + district code + letters + numbers"
        )
        context.user_data['search_type'] = 'vehicle'
    
    elif query.data == 'new_search':
        keyboard = [
            [InlineKeyboardButton("🔍 Search Mobile Number", callback_data='search_mobile')],
            [InlineKeyboardButton("🚗 Search Vehicle Number", callback_data='search_vehicle')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🔄 *Choose what you want to search:*\n\n"
            "Select an option below:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    elif query.data == 'search_again':
        if context.user_data.get('last_search_type') == 'mobile':
            await query.edit_message_text(
                "📱 Please send me a 10-digit mobile number.\n\n"
                "Example: 8585696996"
            )
            context.user_data['search_type'] = 'mobile'
        else:
            await query.edit_message_text(
                "🚗 Please send me a vehicle registration number.\n\n"
                "Example: MH01AB1234"
            )
            context.user_data['search_type'] = 'vehicle'

def clean_mobile_number(number: str) -> str:
    """Clean mobile number by removing +91 and non-digit characters."""
    # Remove +91 if present
    number = number.replace('+91', '')
    # Remove any non-digit characters
    number = re.sub(r'\D', '', number)
    return number

def is_valid_mobile(number: str) -> bool:
    """Check if the number is a valid 10-digit mobile number."""
    cleaned = clean_mobile_number(number)
    return len(cleaned) == 10 and cleaned.isdigit()

def is_valid_vehicle(number: str) -> str:
    """Check if the input looks like a vehicle number and clean it."""
    # Remove spaces and convert to uppercase
    cleaned = re.sub(r'\s+', '', number).upper()
    # Indian vehicle number format: 2 letters + 2 digits + optional letters + 4 digits
    pattern = r'^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$'
    if re.match(pattern, cleaned):
        return cleaned
    return None

def format_mobile_response(data: dict) -> str:
    """Format the mobile lookup API response."""
    if data.get('status') == 'no_data' or data.get('results') == "No Record Found for this number.":
        return f"❌ *No Record Found*\n\nMobile Number: {data.get('API_Info', {}).get('query', 'N/A')}\n\nNo information available for this mobile number."
    
    results = data.get('results', {})
    if isinstance(results, str):
        return f"❌ {results}"
    
    response = f"✅ *Mobile Number Lookup Results*\n\n"
    response += f"📱 *Query:* {data.get('API_Info', {}).get('query', 'N/A')}\n"
    response += f"⏱ *Timestamp:* {data.get('Timestamp', 'N/A')}\n\n"
    response += "─" * 20 + "\n\n"
    
    # Count results (excluding Result N/A entries)
    result_count = 0
    for key, value in results.items():
        if key.startswith('Result') and value.get('name') != 'N/A' and value.get('name') != 'n/a':
            result_count += 1
    
    if result_count == 0:
        response += "❌ No valid records found for this number.\n"
    else:
        response += f"📊 *Found {result_count} record(s)*\n\n"
        
        for key, value in results.items():
            if key.startswith('Result') and value.get('name') != 'N/A' and value.get('name') != 'n/a':
                response += f"*{key.replace('_', ' ')}:*\n"
                response += f"├ 👤 *Name:* {value.get('name', 'N/A')}\n"
                response += f"├ 👨 *Father's Name:* {value.get('father_name', 'N/A')}\n"
                response += f"├ 📱 *Mobile:* {value.get('mobile', 'N/A')}\n"
                response += f"├ 📞 *Alt Mobile:* {value.get('alt_mobile', 'N/A')}\n"
                response += f"├ 📧 *Email:* {value.get('email', 'N/A')}\n"
                response += f"├ 🆔 *Aadhar:* {value.get('aadhar_number', 'N/A')}\n"
                response += f"├ 📡 *Operator:* {value.get('operator', 'N/A')}\n"
                response += f"├ 🌍 *State/Circle:* {value.get('state_circle', 'N/A')}\n"
                response += f"└ 🏠 *Address:* {value.get('address', 'N/A')}\n\n"
    
    response += "\n─" * 20 + "\n"
    response += f"🔹 *Powered by:* {data.get('branding', {}).get('provider', 'TraceXData')}\n"
    response += f"🔹 *Developer:* {data.get('branding', {}).get('developer', '@gaurav_beniwal_0001')}\n"
    
    return response

def format_vehicle_response(data: dict, vehicle_number: str) -> str:
    """Format the vehicle lookup API response."""
    if not data.get('status'):
        return f"❌ *API Error*\n\nUnable to fetch vehicle details for {vehicle_number}."
    
    vehicle_data = data.get('data', {})
    owner_details = vehicle_data.get('owner_details', {})
    vehicle_info = vehicle_data.get('vehicle_info', {})
    registration_details = vehicle_data.get('registration_details', {})
    insurance_and_pucc = vehicle_data.get('insurance_and_pucc', {})
    
    # Check if no data found
    if owner_details.get('owner_name') == 'NA' and vehicle_info.get('registration_number') == 'NA':
        return f"❌ *No Record Found*\n\nVehicle Number: {vehicle_number}\n\nNo information available for this vehicle number."
    
    response = f"✅ *Vehicle Lookup Results*\n\n"
    response += f"🚗 *Vehicle Number:* {vehicle_number}\n\n"
    
    response += "👤 *OWNER DETAILS*\n"
    response += f"├ *Name:* {owner_details.get('owner_name', 'N/A')}\n"
    response += f"├ *Father's Name:* {owner_details.get('father_name', 'N/A')}\n"
    response += f"├ *Present Address:* {owner_details.get('present_address', 'N/A')}\n"
    response += f"└ *Permanent Address:* {owner_details.get('permanent_address', 'N/A')}\n\n"
    
    response += "🚙 *VEHICLE INFORMATION*\n"
    response += f"├ *Registration Number:* {vehicle_info.get('registration_number', 'N/A')}\n"
    response += f"├ *Maker:* {vehicle_info.get('maker', 'N/A')}\n"
    response += f"├ *Model:* {vehicle_info.get('model', 'N/A')}\n"
    response += f"├ *Variant:* {vehicle_info.get('variant', 'N/A')}\n"
    response += f"├ *Vehicle Class:* {vehicle_info.get('vehicle_class', 'N/A')}\n"
    response += f"├ *Vehicle Type:* {vehicle_info.get('vehicle_type', 'N/A')}\n"
    response += f"├ *Fuel Type:* {vehicle_info.get('fuel_type', 'N/A')}\n"
    response += f"├ *Engine Number:* {vehicle_info.get('engine_number', 'N/A')}\n"
    response += f"├ *Chassis Number:* {vehicle_info.get('chassis_number', 'N/A')}\n"
    response += f"├ *Cubic Capacity:* {vehicle_info.get('cubic_capacity', 'N/A')}\n"
    response += f"└ *Commercial:* {'Yes' if vehicle_info.get('is_commercial') else 'No'}\n\n"
    
    response += "📋 *REGISTRATION DETAILS*\n"
    response += f"├ *Registration Date:* {registration_details.get('registration_date', 'N/A')}\n"
    response += f"├ *Manufacturing Date:* {registration_details.get('manufacturing_date', 'N/A')}\n"
    response += f"├ *RTO Code:* {registration_details.get('rto_code', 'N/A')}\n"
    response += f"├ *RTO Name:* {registration_details.get('rto_name', 'N/A')}\n"
    response += f"├ *State:* {registration_details.get('state', 'N/A')}\n"
    response += f"└ *Financer:* {registration_details.get('financer', 'N/A')}\n\n"
    
    response += "🛡 *INSURANCE & PUCC*\n"
    response += f"├ *Insurance Company:* {insurance_and_pucc.get('insurance_company', 'N/A')}\n"
    response += f"├ *Policy Number:* {insurance_and_pucc.get('policy_number', 'N/A')}\n"
    response += f"├ *Valid Upto:* {insurance_and_pucc.get('insurance_valid_upto', 'N/A')}\n"
    response += f"├ *Insurance Expired:* {'Yes' if insurance_and_pucc.get('insurance_expired') else 'No'}\n"
    response += f"├ *PUCC Number:* {insurance_and_pucc.get('pucc_number', 'N/A')}\n"
    response += f"└ *PUCC Valid Upto:* {insurance_and_pucc.get('pucc_valid_upto', 'N/A')}\n"
    
    return response

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and detect if it's mobile or vehicle number."""
    message_text = update.message.text.strip()
    
    # Auto-detect number type
    if is_valid_mobile(message_text):
        context.user_data['last_search_type'] = 'mobile'
        cleaned_number = clean_mobile_number(message_text)
        await lookup_mobile(update, context, cleaned_number)
    
    elif is_valid_vehicle(message_text):
        context.user_data['last_search_type'] = 'vehicle'
        cleaned_vehicle = is_valid_vehicle(message_text)
        await lookup_vehicle(update, context, cleaned_vehicle)
    
    elif context.user_data.get('search_type') == 'mobile':
        if is_valid_mobile(message_text):
            context.user_data['last_search_type'] = 'mobile'
            cleaned_number = clean_mobile_number(message_text)
            await lookup_mobile(update, context, cleaned_number)
        else:
            await update.message.reply_text(
                "❌ *Invalid Mobile Number*\n\nPlease send a valid 10-digit mobile number.\n\nExample: 8585696996",
                parse_mode='Markdown'
            )
    
    elif context.user_data.get('search_type') == 'vehicle':
        cleaned_vehicle = is_valid_vehicle(message_text)
        if cleaned_vehicle:
            context.user_data['last_search_type'] = 'vehicle'
            await lookup_vehicle(update, context, cleaned_vehicle)
        else:
            await update.message.reply_text(
                "❌ *Invalid Vehicle Number*\n\nPlease send a valid Indian vehicle number.\n\nExample: MH01AB1234",
                parse_mode='Markdown'
            )
    
    else:
        keyboard = [
            [InlineKeyboardButton("🔍 Search Mobile Number", callback_data='search_mobile')],
            [InlineKeyboardButton("🚗 Search Vehicle Number", callback_data='search_vehicle')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "❓ *I couldn't identify your input*\n\nPlease select an option below or send a valid number:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    # Reset search type after handling
    context.user_data['search_type'] = None

async def lookup_mobile(update: Update, context: ContextTypes.DEFAULT_TYPE, mobile_number: str):
    """Perform mobile number lookup."""
    await update.message.reply_chat_action(action="typing")
    
    try:
        url = MOBILE_LOOKUP_URL.format(mobile_number)
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        formatted_response = format_mobile_response(data)
        
        # Add new search button
        keyboard = [[InlineKeyboardButton("🔄 New Search", callback_data='new_search')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            formatted_response,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except requests.exceptions.Timeout:
        await update.message.reply_text(
            "⏰ *Timeout Error*\n\nThe API request took too long. Please try again.",
            parse_mode='Markdown'
        )
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(
            f"❌ *Network Error*\n\nFailed to connect to the API. Please try again later.\n\nError: {str(e)}",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ *Unexpected Error*\n\nSomething went wrong. Please try again.\n\nError: {str(e)}",
            parse_mode='Markdown'
        )

async def lookup_vehicle(update: Update, context: ContextTypes.DEFAULT_TYPE, vehicle_number: str):
    """Perform vehicle number lookup."""
    await update.message.reply_chat_action(action="typing")
    
    try:
        url = VEHICLE_LOOKUP_URL.format(vehicle_number)
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        formatted_response = format_vehicle_response(data, vehicle_number)
        
        # Add new search button
        keyboard = [[InlineKeyboardButton("🔄 New Search", callback_data='new_search')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            formatted_response,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except requests.exceptions.Timeout:
        await update.message.reply_text(
            "⏰ *Timeout Error*\n\nThe API request took too long. Please try again.",
            parse_mode='Markdown'
        )
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(
            f"❌ *Network Error*\n\nFailed to connect to the API. Please try again later.\n\nError: {str(e)}",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ *Unexpected Error*\n\nSomething went wrong. Please try again.\n\nError: {str(e)}",
            parse_mode='Markdown'
        )

def main():
    """Start the bot."""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start polling
    print("🤖 Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
