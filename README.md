# ComicForge AI Studio

ComicForge AI Studio is a AI web application that transforms voice or text prompts into continuous, 20-panel comic book storyboards with AI-generated pencil sketch artwork.

## Features
- **ChatGPT Dark Theme**: Minimalist pitch-black interface with centered search input, suggestion pills, and voice input.
- **Voice & Text Inputs**: Hands-free voice recording via `streamlit-mic-recorder` or instant prompt dictation.
- **Instant UI State Transitions**: Smooth navigation flow that removes input widgets during active comic generation.
- **Dynamic 20-Panel Grid**: Equal-height dialogue text boxes and headers with custom sound effects (`ZAP!`, `THWIP!`).
- **Sidebar Chat History**: Saves past generated comics with panel thumbnails, with local disk persistence (`comic_history.json`).
- **Gemini AI Integration**: Enter your optional Google Gemini API key in the sidebar for custom AI script generation.

## Installation & Running Locally

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/comicforge-ai-studio.git
   cd comicforge-ai-studio
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Application**:
   ```bash
   streamlit run app.py
   ```
