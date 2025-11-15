# LLM 911 - AI-Powered Incident Responder

🚀 **Hackathon Project: Daytona Integration Challenge**

## 🎯 What It Does

LLM 911 is an intelligent incident analysis system that automatically analyzes application errors from monitoring tools like **Sentry** and **Galileo**, then provides actionable debugging insights and code fixes using **Anthropic's Claude AI**.

### Key Features
- 🔍 **Automatic Error Analysis**: Ingests Sentry error logs and Galileo performance traces
- 🤖 **AI-Powered Debugging**: Uses Claude 4.5 to analyze incidents and suggest fixes
- 📝 **Code Review Integration**: Provides CodeRabbit-style code analysis
- 🔧 **Reproducible Environments**: One-click Daytona sandbox creation for testing fixes
- 🌐 **Clean Web Interface**: Built with Streamlit for easy interaction

## 🏗️ Architecture

```
LLM 911 System
├── Streamlit Frontend (app.py)
├── AI Analysis Engine (llm_investigator.py)
├── Daytona Integration (create_daytona_sandbox.py)
└── Sample Data (data/)
    ├── sample_sentry.json (Error logs)
    └── sample_galileo.json (Performance traces)
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Anthropic API Key
- (Optional) Daytona Account for sandbox environments

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/arun3676/LLM-911.git
cd LLM-911
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
# Create data/.env file with your API keys
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
DAYTONA_API_KEY=dtn_xxxxxx  # Optional, for sandbox creation
```

4. **Run the application**
```bash
streamlit run app.py
```

5. **Open your browser**
Navigate to `http://localhost:8501`

## 🎮 How to Use

1. **Load Sample Incident**: Click "Load Sample Incident" to ingest test data
2. **Run Analysis**: Click "Run LLM 911" to analyze the incident with AI
3. **Review Results**: View the incident report and code analysis
4. **Test Fixes**: Use Daytona to create a reproducible environment for applying fixes

## 🔧 Daytona Integration

### What Makes This Special

LLM 911 integrates seamlessly with **Daytona** to provide reproducible development environments:

- **One-Click Sandboxes**: Users can spin up a fresh development environment with the exact codebase
- **Isolated Testing**: Apply AI-suggested fixes in a safe, cloud-based workspace
- **Zero Local Setup**: No need to configure local development environments
- **Collaborative Debugging**: Share sandbox environments with team members

### Daytona Command

```bash
# Install Daytona CLI (Windows PowerShell as Administrator)
md -Force "$Env:APPDATA\daytona"; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]'Tls,Tls11,Tls12'; Invoke-WebRequest -URI "https://download.daytona.io/cli/latest/daytona-windows-amd64.exe" -o $Env:APPDATA\daytona\daytona.exe; $env:Path += ";" + $Env:APPDATA + "\daytona"; [Environment]::SetEnvironmentVariable("Path", $env:Path, [System.EnvironmentVariableTarget]::User)

# Create your sandbox
daytona create https://github.com/arun3676/LLM-911.git
```

## 🧪 Tech Stack

- **Frontend**: Streamlit (Python web framework)
- **AI Engine**: Anthropic Claude 4.5 (Sonnet)
- **Environment**: Daytona Sandboxes
- **Data Processing**: Python JSON handling
- **API Integration**: RESTful APIs for monitoring tools

## 💡 Innovation Highlights

1. **AI-Driven Analysis**: Leverages state-of-the-art LLM for incident analysis
2. **Multi-Source Integration**: Combines error logs and performance traces
3. **Reproducible Debugging**: Daytona integration for consistent environments
4. **Developer-Friendly**: Clean UI with actionable insights
5. **Extensible Architecture**: Easy to add new monitoring sources

## 🎯 Use Cases

- **Production Incident Response**: Quickly analyze and debug production issues
- **Development Debugging**: Get AI assistance for complex bugs
- **Code Review Enhancement**: Automated code analysis with AI insights
- **Team Collaboration**: Share reproducible debugging environments
- **Learning Tool**: Understand incident patterns and debugging strategies

## 🔮 Future Enhancements

- Integration with more monitoring tools (DataDog, New Relic)
- Real-time incident monitoring
- Automated fix application
- Team collaboration features
- Historical incident analysis

## 🏆 Hackathon Achievements

- ✅ **Functional AI Analysis**: Working Claude integration for incident analysis
- ✅ **Daytona Integration**: Seamless sandbox provisioning
- ✅ **Clean UI/UX**: Professional Streamlit interface
- ✅ **Complete Workflow**: End-to-end incident analysis solution
- ✅ **Documentation**: Comprehensive setup and usage guides

## 📄 License

MIT License - Feel free to use and contribute!

## 🤝 Contributing

We welcome contributions! Please fork the repository and submit pull requests.

---

**Built with ❤️ for the Daytona Hackathon**
