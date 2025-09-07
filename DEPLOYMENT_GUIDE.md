# 🚀 ITPF Legal Query System - Deployment Guide

This guide will walk you through deploying the full-stack, bilingual legal query application to Netlify.

## 📁 Project Structure

Make sure your project has the following structure:

```
itpf-legal-query/
├── index.html                     # Main HTML file
├── style.css                      # Styles
├── app.js                         # Frontend JavaScript
├── netlify.toml                   # Netlify configuration
├── package.json                   # Node.js configuration
├── indexing_script.js             # One-time indexing script
├── arabic_rules.json              # Arabic legal documents
├── english_rules.json             # English legal documents
├── netlify/
│   └── functions/
│       └── searchFunction.js      # Netlify Function
├── DEPLOYMENT_GUIDE.md            # This file
└── README.md                      # Project documentation
```

## 🔧 Prerequisites

1. **Node.js**: Version 18 or higher
2. **Git**: For version control
3. **Netlify Account**: Free account at [netlify.com](https://netlify.com)
4. **DeepSeek API Key**: Get from DeepSeek dashboard
5. **GitHub Account**: For repository hosting

## 📋 Step-by-Step Deployment

### Step 1: Prepare Your Local Environment

1. **Install Node.js dependencies** (optional, for local development):
   ```bash
   npm install netlify-cli -g
   ```

2. **Replace placeholder legal documents**:
   - Copy your actual legal data from `arabic_legal_rules.json` to `arabic_rules.json`
   - Copy your actual legal data from `english_legal_rules.json` to `english_rules.json`

3. **Test locally** (optional):
   ```bash
   # Start local development server
   npm run serve
   # Or use Python
   python -m http.server 8000
   ```

### Step 2: Create GitHub Repository

1. **Initialize Git repository**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: ITPF Legal Query System"
   ```

2. **Create GitHub repository**:
   - Go to [github.com](https://github.com) and create a new repository
   - Name it: `itpf-legal-query`
   - Make it public or private as needed

3. **Push to GitHub**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/itpf-legal-query.git
   git branch -M main
   git push -u origin main
   ```

### Step 3: Index Legal Documents (One-Time Setup)

**⚠️ IMPORTANT: Run this BEFORE deploying to Netlify**

1. **Set your DeepSeek API key**:
   ```bash
   # On macOS/Linux
   export DEEPSEEK_API_KEY="your-actual-deepseek-api-key-here"
   
   # On Windows
   set DEEPSEEK_API_KEY=your-actual-deepseek-api-key-here
   ```

2. **Update API endpoint** in `indexing_script.js`:
   - Replace `https://api.deepseek.com/v1/index` with actual DeepSeek indexing endpoint

3. **Run the indexing script**:
   ```bash
   node indexing_script.js
   ```

4. **Verify indexing success**:
   - Look for "✅ Successfully indexed" messages
   - Both Arabic and English documents should be indexed

### Step 4: Deploy to Netlify

#### Option A: Deploy via Netlify Dashboard (Recommended)

1. **Log into Netlify**:
   - Go to [app.netlify.com](https://app.netlify.com)
   - Sign in or create account

2. **Create new site**:
   - Click "Add new site" → "Import an existing project"
   - Choose "GitHub" and authorize Netlify
   - Select your `itpf-legal-query` repository

3. **Configure build settings**:
   - **Build command**: `echo 'No build process required'`
   - **Publish directory**: `.` (root directory)
   - **Functions directory**: `netlify/functions`
   - Click "Deploy site"

4. **Configure environment variables**:
   - Go to "Site settings" → "Environment variables"
   - Add the following variables:

   | Variable Name | Value | Notes |
   |---------------|-------|-------|
   | `DEEPSEEK_API_KEY` | Your DeepSeek API key | Required |
   | `DEEPSEEK_SEARCH_ENDPOINT` | DeepSeek search endpoint | Optional, has default |
   | `NODE_ENV` | `production` | Optional |

5. **Deploy**:
   - Click "Deploy site"
   - Wait for deployment to complete
   - Your site will be available at `https://your-site-name.netlify.app`

#### Option B: Deploy via Netlify CLI

1. **Install Netlify CLI**:
   ```bash
   npm install -g netlify-cli
   ```

2. **Login to Netlify**:
   ```bash
   netlify login
   ```

3. **Initialize Netlify site**:
   ```bash
   netlify init
   ```

4. **Set environment variables**:
   ```bash
   netlify env:set DEEPSEEK_API_KEY "your-actual-api-key"
   netlify env:set DEEPSEEK_SEARCH_ENDPOINT "your-search-endpoint"
   ```

5. **Deploy**:
   ```bash
   netlify deploy --prod
   ```

### Step 5: Configure Custom Domain (Optional)

1. **Purchase domain** (if you don't have one)

2. **Add custom domain**:
   - Go to "Site settings" → "Domain management"
   - Click "Add custom domain"
   - Follow the DNS configuration instructions

3. **Enable HTTPS**:
   - Netlify automatically provisions SSL certificates
   - Ensure "Force HTTPS" is enabled

### Step 6: Test Your Deployment

1. **Access your site**:
   - Visit your Netlify URL: `https://your-site-name.netlify.app`

2. **Test functionality**:
   - ✅ Language toggle works (EN ↔ عربي)
   - ✅ Search form accepts input
   - ✅ Search returns results from DeepSeek API
   - ✅ Results display properly in both languages
   - ✅ Error handling works

3. **Test API endpoint directly** (optional):
   ```bash
   curl -X POST https://your-site-name.netlify.app/.netlify/functions/searchFunction \\
     -H "Content-Type: application/json" \\
     -d '{\"query\": \"What is tent pegging?\", \"language\": \"en\"}'
   ```

## 🔧 Troubleshooting

### Common Issues

1. **"Function not found" error**:
   - Check that `netlify/functions/searchFunction.js` exists
   - Verify Netlify build completed successfully
   - Check function logs in Netlify dashboard

2. **"API key not configured" error**:
   - Verify `DEEPSEEK_API_KEY` environment variable is set
   - Redeploy after adding environment variables

3. **Search returns no results**:
   - Ensure indexing script ran successfully
   - Check DeepSeek API endpoint URLs are correct
   - Verify documents were indexed in correct language

4. **CORS errors**:
   - Check `netlify.toml` configuration
   - Ensure CORS headers are properly set

5. **Arabic text not displaying correctly**:
   - Verify Arabic fonts are loading
   - Check RTL direction is applied

### Debug Steps

1. **Check Netlify function logs**:
   - Go to Netlify dashboard → Functions → View logs

2. **Check browser console**:
   - Open Developer Tools → Console
   - Look for JavaScript errors

3. **Test API endpoints**:
   - Use browser Network tab or Postman
   - Verify requests/responses

## 🔄 Making Updates

1. **Code changes**:
   ```bash
   git add .
   git commit -m "Update: description of changes"
   git push origin main
   ```
   - Netlify will automatically redeploy

2. **Environment variable changes**:
   - Update in Netlify dashboard
   - Trigger manual redeploy if needed

3. **Re-indexing documents**:
   - Run `node indexing_script.js` locally with updated documents
   - No need to redeploy the site

## 🔐 Security Considerations

1. **API Key Protection**:
   - ✅ API key stored as environment variable
   - ✅ Never committed to repository
   - ✅ Only accessible to Netlify Functions

2. **Input Validation**:
   - ✅ Query length limits enforced
   - ✅ HTML content escaped
   - ✅ XSS protection implemented

3. **Rate Limiting** (recommended):
   - Consider implementing rate limiting for API calls
   - Monitor DeepSeek API usage

## 📊 Monitoring and Analytics

1. **Netlify Analytics**:
   - Enable in Netlify dashboard for traffic insights

2. **Function Monitoring**:
   - Check function invocation logs
   - Monitor response times and errors

3. **User Feedback**:
   - Consider adding user feedback mechanism
   - Monitor search success rates

## 🆘 Support

If you encounter issues:

1. **Check logs**: Netlify dashboard → Functions → Logs
2. **Verify configuration**: Environment variables and build settings
3. **Test locally**: Use `netlify dev` for local development
4. **Documentation**: [Netlify Functions Docs](https://docs.netlify.com/functions/overview/)

---

## 🎉 Congratulations!

Your ITPF Legal Query System is now live and ready to serve bilingual legal searches powered by AI!

**Site URL**: `https://your-site-name.netlify.app`

### Next Steps:
- Share the URL with users
- Monitor usage and performance
- Consider adding more legal documents
- Implement user feedback collection
- Add analytics tracking