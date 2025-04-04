# Verilog Generator & Optimizer

A Streamlit application that uses Google's Gemini AI to generate and optimize Verilog code for systolic arrays and other hardware designs.

## Deployment Guide

This guide will walk you through deploying your Streamlit app from local development to a live website.

### Prerequisites

- A Google API key for Gemini AI
- Git installed on your system (for some deployment methods)
- Python 3.9+ installed on your system

### Option 1: Deploy to Streamlit Cloud (Recommended)

Streamlit Cloud is the easiest way to deploy Streamlit apps:

1. **Create a GitHub repository**
   - Create a new repository on GitHub
   - Push your code to the repository:
     ```
     git init
     git add .
     git commit -m "Initial commit"
     git branch -M main
     git remote add origin https://github.com/yourusername/your-repo-name.git
     git push -u origin main
     ```

2. **Sign up for Streamlit Cloud**
   - Go to [Streamlit Cloud](https://streamlit.io/cloud)
   - Sign in with your GitHub account

3. **Deploy your app**
   - Click "New app"
   - Select your repository, branch, and the main file (streamlit_app.py)
   - Under "Advanced settings", add your API key as a secret:
     - Key: `API_KEY`
     - Value: Your Google API key
   - Click "Deploy"

4. **Access your deployed app**
   - Once deployed, you'll get a URL like `https://yourusername-your-repo-name-streamlit-app.streamlit.app`

### Option 2: Deploy to Heroku

1. **Create a Procfile**
   - Create a file named `Procfile` (no extension) with the content:
     ```
     web: streamlit run streamlit_app.py --server.port=$PORT
     ```

2. **Create a runtime.txt file**
   - Create a file named `runtime.txt` with the content:
     ```
     python-3.9.18
     ```

3. **Install Heroku CLI and deploy**
   - Install [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
   - Login to Heroku: `heroku login`
   - Create a new Heroku app: `heroku create your-app-name`
   - Set the API key: `heroku config:set API_KEY=your-api-key`
   - Deploy your app: `git push heroku main`
   - Open your app: `heroku open`

### Option 3: Deploy to Render

1. **Sign up for Render**
   - Go to [Render](https://render.com/) and create an account

2. **Create a new Web Service**
   - Click "New" and select "Web Service"
   - Connect your GitHub repository
   - Configure the service:
     - Name: Choose a name for your app
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `streamlit run streamlit_app.py`
   - Add environment variable:
     - Key: `API_KEY`
     - Value: Your Google API key
   - Click "Create Web Service"

## Local Development

To run the app locally:

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your API key:
   ```
   API_KEY=your-api-key
   ```

3. Run the app:
   ```
   streamlit run streamlit_app.py
   ```

## Important Notes

- **API Key Security**: Never commit your API key to your repository. Always use environment variables or secrets management.
- **Costs**: Be aware that using the Gemini API may incur costs depending on your usage.
- **Performance**: The app may run slower on free tiers of hosting services due to limited resources.