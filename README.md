# El Plan STEM

El Plan STEM is a Django-based web application that combines the excitement of Formula 1 with engaging, AI-powered STEM education. Whether you're a student learning physics through lap times or an F1 enthusiast curious about race analytics, this project delivers a powerful, interactive experience.

This repository is originally based on [this](https://github.com/Z33xD/El-Plan-STEM) repository.

---

## Features

### F1-Themed Educational Chatbot
- Teaches STEM concepts (Science, Technology, Engineering, Mathematics) using real F1 data.
- Auto-generates quiz-style questions based on:
  - Lap times
  - Pit stops
  - Driver statistics
- Evaluates answers with explanations using Formula 1 analogies.
- Maintains conversational history for context-rich feedback.

### General F1 Assistant
- Chat with a bot to retrieve real-time facts and data about drivers, races, and circuits.
- Uses semantic vector search with sentence embeddings for intelligent query handling.

### Notes System
- Lets users create, save, and manage notes for studying or strategy planning.

### Graphing Module
- Visualizes F1 data such as speed trends, pit stop frequencies, or momentum shifts.

---

## Tech Stack

- **Backend:** Django 5.2.1
- **Database:** MongoDB (via `django-mongodb-backend`)
- **AI Integration:** Google Gemini (Gemini 2.5 Flash)
- **Frontend:** Django templates + static files (HTML/CSS/JS)

---

## Project Structure

```
El-Plan-STEM/
├── config/
├── project/
│   ├── backend/          # Django project settings (core config)
│   ├── core/             # Main website (home, about, etc.)
│   ├── chatbot/          # Chatbot system + AI services
│   ├── explorer/        # Explorer feature/module
│   ├── static/          # CSS, JS, images
│   └── templates/       # HTML templates
├── requirements.txt
├── README.md
├── .env.example
├── .env
```

---

## Setup Instructions

1. **Install Python 3.14**

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the environment**
   ```bash
   .\venv\Scripts\Activate.ps1
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the server**
   ```bash
   cd project
   python manage.py runserver
   ```
   > This is a development server, and not to be used in a production setting.
   > The project would run at http://127.0.0.1:8000/.

6. **Stop the server, once you're done using it**
   ```mathematica
   ctrl + C
   ```

7. **Deactivate the environment**
   ```bash
   deactivate
   ```

---

## Routes Overview

| Route                    | Description                       |
| ------------------------ | --------------------------------- |
| `/`                      | Home page                         |
| `/chatbot/`              | Main chatbot interface            |
| `/about/`                | About the project                 |

---

## Acknowledgements

Thanks to the teams behind:
- Google Generative AI
- Ergast's Formula 1 open datasets
- Django & MongoDB communities

---