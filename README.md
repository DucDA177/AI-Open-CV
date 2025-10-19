# AI CV Builder (Streamlit)

This project is a Streamlit-based web app that generates or improves IT CVs using OpenAI's API. You can run it locally using **Anaconda** or **Miniconda**.

---

## 🧩 1. Prerequisites

* Windows, macOS, or Linux
* **Python 3.10+** (recommended: 3.11)
* **Anaconda** or **Miniconda** installed
* An **OpenAI API key** (or compatible endpoint)

---

## 🐍 2. Install Anaconda

### 🔹 Windows

1. Go to the official page: [https://www.anaconda.com/download](https://www.anaconda.com/download)
2. Download the **Windows Installer (64-bit)**.
3. Run the installer → choose **Add Anaconda to PATH** (optional, but convenient).
4. Finish setup.

### 🔹 macOS / Linux

1. Visit the same link and download the version for your OS.
2. Open Terminal and run the downloaded installer, for example:

   ```bash
   bash ~/Downloads/Anaconda3-2025.x.x-MacOSX-x86_64.sh
   ```
3. Follow the on-screen instructions and restart your terminal.

Verify installation:

```bash
conda --version
```

If you see a version number, Anaconda is ready.

---

## 💻 3. Open Conda Prompt in Your Working Folder

### 🪟 On Windows

#### ✅ Option 1: From File Explorer (Recommended)

1. Open your project folder (where `app.py` and `requirements.txt` are located).
2. Right-click inside the empty space.
3. Choose **“Open in Terminal”** (Windows 11) or **“Open Command Window here”**.
4. In the terminal, activate Anaconda:

   ```powershell
   conda activate base
   ```

   or if you already created your environment:

   ```powershell
   conda activate aicv
   ```

#### ✅ Option 2: From Start Menu

1. Press **Start → Anaconda Prompt**.
2. Navigate to your project folder:

   ```bash
   cd C:\Users\<YourName>\Documents\aicv-builder
   ```
3. Then activate your environment.

### 🍎 On macOS / Linux

1. Open **Terminal**.
2. Navigate to your project:

   ```bash
   cd ~/Documents/aicv-builder
   ```
3. Activate the environment:

   ```bash
   conda activate aicv
   ```

---

## 🧱 4. Create and Activate Environment

```bash
conda create -n aicv python=3.11 -y
conda activate aicv
```

---

## 📦 5. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:

* `streamlit` → Web interface
* `openai` → API calls
* `reportlab`, `python-docx`, `pdfplumber`, `docx2txt` → File handling & export

---

## 🔑 6. Configure Environment Variables

### Windows PowerShell

```powershell
$env:OPENAI_API_KEY="YOUR_KEY_HERE"
# Optional (if using custom endpoint)
# $env:OPENAI_BASE_URL="https://api.openai.com/v1"
# $env:OPENAI_MODEL="gpt-4o-mini"
```

### macOS/Linux

```bash
export OPENAI_API_KEY="YOUR_KEY_HERE"
# export OPENAI_BASE_URL="https://api.openai.com/v1"
# export OPENAI_MODEL="gpt-4o-mini"
```

---

## 🖋 7. (Optional) Add Font for Vietnamese PDF Export

1. Download **DejaVuSans.ttf**.
2. Place it next to `app.py`.
3. The app will automatically use it when generating PDFs.

---

## 🚀 8. Run the Application

In your project folder:

```bash
streamlit run app.py
```

Streamlit will display a local URL like:

```
Local URL: http://localhost:8501
```

Open it in your browser.

---

## 🧭 9. Using the App

1. Expand **"Thông tin cá nhân"** → Fill in details.
2. Expand **"Mô tả công việc (JD)"** → Paste your job description.
3. (Optional) Upload your existing CV (`.docx`, `.pdf`, `.txt`).
4. Choose one of:

   * 🆕 *Tạo CV mới*
   * ✨ *Cải thiện theo JD*
   * 📄 *Cải thiện từ tệp tải lên*
5. Edit the generated CV and download as **Word** or **PDF**.

---

## 🤖 10. AI Chatbot Assistant

The application includes an intelligent AI chatbot that provides real-time CV and career guidance.

### 🎯 Chatbot Features

#### **Quick Action Buttons**
- **💡 Tư vấn CV**: Get personalized CV improvement suggestions
- **📋 Phân tích JD**: Analyze job descriptions and extract key requirements
- **📊 So sánh CV-JD**: Compare your CV with job descriptions to identify matches and gaps
- **🎯 Kỹ năng cần**: Identify skills you need to develop based on target jobs

#### **File Upload Support**
- **Documents**: Upload CVs and JDs in `.txt`, `.md`, `.docx`, `.pdf` formats
- **Images**: Upload screenshots of CVs or JDs in `.jpg`, `.jpeg`, `.png` formats
- **Automatic Processing**: Files are automatically analyzed and integrated into the conversation

#### **Advanced Chat Capabilities**
- **Multi-line Input**: Large text area for detailed questions and descriptions
- **Context Awareness**: Uses your profile information for personalized responses
- **Real-time Responses**: Instant AI-powered guidance and suggestions
- **Conversation History**: Maintains chat history during your session

### 💬 How to Use the Chatbot

1. **Access the Chatbot**: The chat interface is located in the left sidebar, which opens automatically when the app loads.

2. **Enable Chat**: Make sure the "Bật trợ lý chat" checkbox is checked to activate the chatbot.

3. **Quick Actions**: Use the quick action buttons for common tasks:
   - Click "💡 Tư vấn CV" for CV improvement suggestions
   - Click "📋 Phân tích JD" to analyze job descriptions
   - Click "📊 So sánh CV-JD" to compare your CV with job requirements
   - Click "🎯 Kỹ năng cần" to identify skill gaps

4. **Upload Files**: Use the file uploader to analyze documents or images:
   - Upload your CV for personalized feedback
   - Upload job descriptions for detailed analysis
   - Upload screenshots of CVs or JDs for image-based analysis

5. **Ask Questions**: Use the text area to ask specific questions about:
   - CV formatting and content
   - Job application strategies
   - Interview preparation
   - Career development advice
   - Skill gap analysis

### 📁 Supported File Types

| File Type | Formats | Purpose |
|-----------|---------|---------|
| Documents | `.txt`, `.md`, `.docx`, `.pdf` | CV analysis, JD extraction |
| Images | `.jpg`, `.jpeg`, `.png` | Screenshot analysis, document images |

### 🔧 Technical Features

#### **Advanced AI Capabilities**
- **Retry Mechanisms**: Automatic retry with exponential backoff for API reliability
- **Batching**: Efficient processing of multiple requests for better performance
- **Function Calling**: Structured responses for CV analysis and comparison
- **Error Handling**: Comprehensive error recovery and user-friendly messages

#### **Performance Optimization**
- **Batch Processing**: Groups similar requests to reduce API calls
- **Caching**: Maintains conversation context for relevant responses
- **Rate Limiting**: Smart handling of API limits with progressive delays

### 💡 Best Practices

1. **Provide Context**: Fill in your personal information in the main form for more personalized chatbot responses.

2. **Upload Files**: Upload your CV and target job descriptions for the most accurate analysis.

3. **Be Specific**: Ask detailed questions for more helpful responses.

4. **Use Quick Actions**: Start with quick action buttons for common scenarios.

5. **Review Suggestions**: The chatbot provides actionable suggestions - implement them in your CV.

### 🚨 Troubleshooting Chatbot Issues

| Issue | Solution |
|-------|----------|
| Chatbot not responding | Check if "Bật trợ lý chat" is enabled |
| File upload not working | Ensure file is in supported format and under size limits |
| Slow responses | The AI is processing complex analysis - please wait |
| Error messages | Check your internet connection and API key configuration |

### 🎓 Example Use Cases

1. **CV Improvement**: Upload your CV and ask "How can I improve my CV for a Python developer position?"

2. **JD Analysis**: Upload a job description and ask "What are the key requirements for this role?"

3. **Skill Gap Analysis**: Provide your skills and a target JD to identify what you need to learn.

4. **Interview Preparation**: Ask "What technical questions should I expect for a backend developer interview?"

5. **Career Advice**: "What's the best career path for someone with my skills and experience?"

---

## 🧹 11. Troubleshooting

| Problem                          | Solution                                      |
| -------------------------------- | --------------------------------------------- |
| `conda: command not found`       | Restart terminal after installing Anaconda    |
| `ModuleNotFoundError`            | Re-run `pip install -r requirements.txt`      |
| `OpenAI API error 401`           | Verify your `OPENAI_API_KEY`                  |
| `Vietnamese text missing in PDF` | Add `DejaVuSans.ttf` font                     |
| `Port 8501 in use`               | Run `streamlit run app.py --server.port 8502` |

---

## ✅ Summary

| Step         | Command                               |
| ------------ | ------------------------------------- |
| Create env   | `conda create -n aicv python=3.11 -y` |
| Activate env | `conda activate aicv`                 |
| Install deps | `pip install -r requirements.txt`     |
| Run app      | `streamlit run app.py`                |

---

## 💡 Tips

* You can open VS Code and use its **Integrated Terminal** (it automatically starts in your project folder).
* To stop the app: press **Ctrl + C**.
* To update packages later: `pip install --upgrade streamlit openai`.

---

**Developed by OpenCV Team
