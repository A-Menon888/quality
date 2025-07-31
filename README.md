# 🎯 Quality Assurance Assistant

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-orange.svg)](https://streamlit.io/)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini-green.svg)](https://deepmind.google/technologies/gemini/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent Quality Assurance assistant that combines semantic tool recommendation with document-based question answering. Powered by Google's Gemini model and featuring a sleek Streamlit interface.

## 🌟 Features

- 🔍 **Smart Tool Recommendations**: Semantically matches your questions with appropriate quality tools
- 📚 **Document-Based Answers**: Searches through your QA documentation for relevant information
- 🔗 **Source Citations**: Every answer includes citations to source documents
- ⚡ **Real-Time Processing**: Async processing with parallel tool recommendation
- 🎨 **Modern UI**: Clean, responsive Streamlit interface
- 💾 **Efficient Caching**: LRU cache for quick responses to similar queries

## 🛠️ Quality Tools Covered

- **Pareto Chart**: Prioritize issues based on frequency
- **5-Why/Fishbone**: Root cause analysis
- **Cp/Cpk Analysis**: Process capability evaluation
- **Control Chart**: Monitor process variation
- **Histogram**: Analyze data distribution

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/A-Menon888/quality.git
   cd quality
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   - Create a `.env` file in the project root
   - Add your Gemini API key:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```

4. **Prepare your documents**
   - Place your PDF documents in the `pdf/` folder
   - Run the indexing script:
     ```bash
     python embed_index.py
     ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

## 💻 Usage

1. **Ask Questions**: Type your quality-related questions in the input box
2. **Get Recommendations**: The system will suggest appropriate quality tools
3. **View Sources**: Click "View Sources" to see document references
4. **Explore Tips**: Check the sidebar for usage tips and examples

### Example Questions

- "What are the key steps in quality assurance testing?"
- "How can I identify the most common defects?"
- "What tool should I use to analyze process variation?"
- "How do I investigate the root cause of a problem?"

## 🏗️ Architecture

```
├── app.py              # Streamlit UI
├── qa_bot.py          # Main QA logic
├── tool_recommender.py # Tool recommendation system
├── embed_index.py     # Document indexing
├── requirements.txt   # Dependencies
└── pdf/              # Your QA documents
```

## ⚙️ Technical Details

- **Vector Search**: FAISS for efficient document retrieval
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **LLM**: Google Gemini
- **UI**: Streamlit
- **Async Processing**: Python asyncio

## 🔒 Security

- Environment variables for API keys
- Safe FAISS deserialization
- Proper error handling

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini API for powerful language processing
- Streamlit for the amazing UI framework
- FAISS for efficient vector search
- LangChain for the document processing pipeline

---

<p align="center">
  Made for Quality Assurance Professionals and MSME's by Aayush and Rohit.
</p>
