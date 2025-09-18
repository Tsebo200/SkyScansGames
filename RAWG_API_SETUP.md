# SkyScansGames - RAWG API Setup

## Getting Your RAWG API Key

To use real game data, you need a RAWG API key:

1. **Visit RAWG API Docs**: Go to [https://rawg.io/apidocs](https://rawg.io/apidocs)
2. **Create Account**: Sign up for a free account if you don't have one
3. **Get API Key**: Your API key will be displayed in the API documentation
4. **Copy the Key**: It will look something like: `1234567890abcdef1234567890abcdef`

## Setting Up Your API Key

### Option 1: Environment Variable (Recommended)
```bash
# Set the environment variable
export RAWG_API_KEY=your_actual_api_key_here

# Then run the backend
cd backend
python main.py
```

### Option 2: .env File (Easier)
1. Edit the `backend/.env` file
2. Replace `your_rawg_api_key_here` with your actual API key:
```
RAWG_API_KEY=1234567890abcdef1234567890abcdef
STEAM_API_KEY=
```

3. Install python-dotenv:
```bash
pip install python-dotenv
```

4. Run the backend:
```bash
cd backend
python main.py
```

## Demo Mode

If you don't have an API key yet, the system will automatically fall back to **demo mode** with sample games:
- The Legend of Zelda: Breath of the Wild
- The Witcher 3: Wild Hunt
- God of War Ragnarök
- Elden Ring
- Red Dead Redemption 2

The demo mode allows you to test all functionality while you get your API key set up.

## Testing the Setup

1. Start the backend server:
```bash
cd backend
python main.py
```

2. Start the frontend:
```bash
cd frontend
npm start
```

3. Search for games like "god", "witcher", "zelda" - you should see results!

## Troubleshooting

- **Still getting 401 errors?** Make sure your API key is correctly set in the .env file or environment variable
- **No games showing?** Check the backend logs for any error messages
- **Demo mode not working?** The fallback should work automatically when the API key is invalid

## Rate Limits

RAWG API has rate limits:
- Free tier: 20,000 requests per month
- Paid tiers available for higher limits

The system includes basic error handling for rate limits.