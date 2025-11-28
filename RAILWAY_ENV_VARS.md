# Required Environment Variables for Railway

You need to set these environment variables in Railway for the app to work:

## Required Variables

1. **ANTHROPIC_API_KEY**
   - Your Anthropic API key with available credits
   - Get from: https://console.anthropic.com/account/keys
   - Set in Railway: Settings → Variables → Add Variable

2. **AWS_ACCESS_KEY_ID** (optional)
   - If using AWS features
   
3. **AWS_SECRET_ACCESS_KEY** (optional)
   - If using AWS features

## How to Set in Railway

1. Go to your Railway project dashboard
2. Click on "eloquent-liberation" service
3. Go to "Variables" tab
4. Click "Add Variable"
5. Add:
   - Variable name: `ANTHROPIC_API_KEY`
   - Value: Your API key (starts with sk-ant-api...)
6. The deployment will automatically restart

## Verify Your API Key

Make sure your API key:
- Has available credits (check at https://console.anthropic.com/settings/billing)
- Is not expired
- Has the correct permissions

## Test After Setting

After setting the variable, the app should:
1. Automatically redeploy
2. Be able to connect to Anthropic API
3. Show no API errors in the Settings panel