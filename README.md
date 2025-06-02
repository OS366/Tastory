# Tastory - The Food Search Engine 🔍🍳

<p align="center">
  <img src="frontend/public/images/logo.png" alt="Tastory Logo" width="120">
</p>

<p align="center">
  <strong>The world's most advanced food search engine.</strong><br>
  Search 230,000+ recipes instantly using AI-powered semantic search.
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#why-tastory">Why Tastory</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#getting-started">Getting Started</a>
</p>

---

## 🚀 What is Tastory?

Tastory is a specialized **food search engine** that understands what you're looking for, not just keyword matching. Built specifically for food and recipes, it delivers instant, relevant results whether you search for:

- **Ingredients**: "chicken and broccoli"
- **Dietary needs**: "gluten-free desserts"
- **Time constraints**: "30 minute meals"
- **Cuisine types**: "authentic Thai curry"
- **Cooking methods**: "air fryer recipes"
- **Occasions**: "romantic dinner for two"

## ✨ Features

### 🔍 **Advanced Search Capabilities**

- **Semantic Search**: Understands context and intent, not just keywords
- **Multi-language Support**: Search in English, Spanish, French, German, Italian, or Portuguese
- **Smart Suggestions**: Auto-complete based on popular searches
- **Voice Search**: Hands-free searching while cooking

### 🎯 **Search Engine Features**

- **Lightning Fast**: Results in under 2 seconds
- **Smart Ranking**: AI sorts by relevance, not just popularity
- **Visual Results**: Image-first design for quick browsing
- **Filter & Refine**: By cuisine, diet, time, difficulty

### 🗣️ **Interactive Features**

- **Text-to-Speech**: Recipe narration in multiple languages
- **Cooking Mode**: Step-by-step guidance (coming soon)
- **Favorites**: Save and organize your recipe collection
- **Dark Mode**: Easy on the eyes during late-night cooking

## 🤔 Why Tastory vs Generic Search?

| Feature              | Google/Bing      | ChatGPT        | **Tastory**           |
| -------------------- | ---------------- | -------------- | --------------------- |
| Food-specific search | ❌ Generic       | ❌ Generic     | ✅ **Built for food** |
| Recipe database      | ❌ Crawled web   | ❌ No database | ✅ **230K+ curated**  |
| Visual browsing      | ⚠️ Mixed results | ❌ Text only   | ✅ **Image-first**    |
| Cooking features     | ❌ None          | ❌ None        | ✅ **TTS, timers**    |
| Search speed         | ⚠️ Variable      | ⚠️ Slow        | ✅ **<2 seconds**     |
| Dietary filters      | ❌ Manual        | ❌ Manual      | ✅ **Built-in**       |

## 🛠️ Tech Stack

- **Frontend**: React, Material-UI, Webpack
- **Backend**: Python, Flask, MongoDB Atlas
- **AI/ML**: Sentence Transformers (all-MiniLM-L6-v2)
- **Database**: MongoDB with vector search indexes
- **Search**: Hybrid approach (semantic + text search)

## 🚦 Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+
- MongoDB Atlas account

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/tastory.git
   cd tastory
   ```

2. **Set up the backend**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment**

   ```bash
   cp .env.example .env
   # Edit .env with your MongoDB connection string
   ```

4. **Set up the frontend**

   ```bash
   cd frontend
   npm install
   ```

5. **Run the application**

   Terminal 1 - Backend:

   ```bash
   python app.py
   ```

   Terminal 2 - Frontend:

   ```bash
   cd frontend
   npm start
   ```

6. **Open your browser**
   Navigate to `http://localhost:3000`

## 🎯 Search Examples

Try these searches to see Tastory in action:

- **By Ingredient**: "salmon with lemon"
- **By Time**: "quick breakfast under 15 minutes"
- **By Diet**: "keto chocolate cake"
- **By Cuisine**: "authentic pad thai"
- **By Method**: "instant pot chicken"
- **By Occasion**: "birthday party appetizers"

## 🔮 Future Roadmap

- [ ] **Advanced Filters**: Calorie ranges, macro tracking
- [ ] **Recipe Collections**: User-curated lists
- [ ] **Meal Planning**: Weekly meal prep assistance
- [ ] **Shopping Lists**: Ingredient aggregation
- [ ] **Social Features**: Share and rate recipes
- [ ] **API Access**: For developers and partners

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

<p align="center">
  <strong>Tastory - The Food Search Engine</strong><br>
  Making recipe discovery as easy as web search.
</p>
