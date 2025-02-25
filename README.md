# Chomsky Articles Q&A Generator

A Python-based automation tool that scrapes articles from [Chomsky's website](https://chomsky.info/articles/), extracts speaker-specific content (e.g., Noam Chomsky, Vijay Prashad), and generates unique question-and-answer pairs for each article using the Grok API. The generated Q&A pairs can be previewed via a user-friendly Streamlit interface and exported as a PDF for further study or distribution.

## Features

- **Article Scraping & Parsing:**  
  Automatically fetch and parse articles, identifying key speakers and segmenting text accordingly.

- **Intelligent Q&A Generation:**  
  Utilizes the Grok API to generate multiple unique Q&A pairs from each article. Customizable prompts ensure:
  - A higher frequency of Q&A pairs
  - Detailed answers (minimum 3-5 lines per answer)
  - Questions that cover different angles (historical, theoretical, critical, etc.)

- **Streamlit Front End:**  
  An interactive web interface to:
  - Input article URLs or choose from a pre-defined list.
  - Preview generated Q&A pairs.
  - Edit or regenerate specific Q&A pairs based on feedback.

- **PDF Export:**  
  Compiled output can be exported as a PDF, complete with clear labeling (article title, speaker names, etc.) for easy reading and distribution.

## Prerequisites

- **Python 3.8+**  
- **Grok API Key** for accessing the Grok API service

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/choppagunasundar73/chomsky_articles.git
   cd chomsky_articles
Set Up Your Environment:

(Optional but recommended) Create a virtual environment:
bash
Copy
Edit
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install Dependencies:

bash
Copy
Edit
pip install -r requirements.txt
Configure the Grok API Key:

Obtain your Grok API key.
Set the API key in your environment:
bash
Copy
Edit
export GROK_API_KEY='your_grok_api_key_here'
Alternatively, update your configuration file (e.g., config.py) with your Grok API key.
Usage
Run the Streamlit Application:

bash
Copy
Edit
streamlit run app.py
Interact with the Interface:

Input the URL of the Chomsky article you want to process.
Click the "Generate Q&A" button to:
Scrape and parse the article.
Extract speaker-specific content.
Generate unique Q&A pairs using the Grok API.
Preview and, if necessary, edit or regenerate the Q&A pairs.
Export the final output as a PDF.
Advanced Customization
Increase Q&A Frequency & Uniqueness:

Adjust your prompt to request more distinct Q&A pairs (e.g., "Generate 10 distinct Q&A pairs").
Tweak API parameters such as temperature and top_p to encourage varied responses.
Use multiple prompt variations targeting different themes or segments of the article.
Implement post-processing deduplication to remove similar or redundant Q&A pairs.
Feedback Loop Integration:

Use Streamlit widgets to gather user feedback on the generated Q&A pairs.
Use this feedback to refine and re-run the prompt for improved results.
Contributing
Contributions, suggestions, and improvements are welcome!

Fork the repository.
Create your feature branch: git checkout -b feature/my-new-feature
Commit your changes: git commit -am 'Add some feature'
Push to the branch: git push origin feature/my-new-feature
Open a pull request.
License
This project is licensed under the MIT License - see the LICENSE file for details.

Acknowledgments
Thanks to the Grok API team and the developers of the Python libraries used in this project.
Special thanks to the open-source community for their continuous contributions.
