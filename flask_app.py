from flask import Flask, render_template, request, jsonify
import os
import threading
from rag_chatbot import BibliothequeRagBot

app = Flask(__name__)

# Instance globale du bot (sera initialisée au démarrage)
bot = None

@app.route('/')
def index():
    """Page d'accueil avec l'interface de chat."""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    """Endpoint pour poser une question au bot."""
    question = request.json.get('question', '')
    
    if not question:
        return jsonify({'error': 'Question vide'}), 400
    
    try:
        answer, sources = bot.ask(question)
        
        # Extraction des métadonnées des sources
        sources_info = []
        for doc in sources:
            sources_info.append({
                'library': doc.metadata.get('library', 'N/A'),
                'source': doc.metadata.get('source', 'N/A'),
                'content': doc.page_content[:100] + '...' if len(doc.page_content) > 100 else doc.page_content
            })
        
        return jsonify({
            'answer': answer,
            'sources': sources_info
        })
    
    except Exception as e:
        print(f"Erreur lors du traitement de la question: {e}")
        return jsonify({'error': f'Erreur: {str(e)}'}), 500

def create_templates():
    """Crée les fichiers de template pour Flask."""
    os.makedirs('templates', exist_ok=True)
    
    # Fichier index.html
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write("""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Assistant Bibliothèques Paris-Saclay</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .chat-container {
            height: 400px;
            border: 1px solid #ccc;
            padding: 10px;
            overflow-y: auto;
            margin-bottom: 10px;
            border-radius: 5px;
        }
        .message {
            margin-bottom: 10px;
            padding: 8px 15px;
            border-radius: 18px;
            max-width: 70%;
            clear: both;
        }
        .user-message {
            background-color: #DCF8C6;
            float: right;
        }
        .bot-message {
            background-color: #F1F0F0;
            float: left;
        }
        .sources {
            font-size: 0.8em;
            color: #666;
            margin-top: 5px;
            clear: both;
        }
        .input-container {
            display: flex;
            gap: 10px;
        }
        #questionInput {
            flex: 1;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        button {
            padding: 10px 15px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        .loading {
            display: none;
            text-align: center;
            margin: 10px 0;
        }
        header {
            text-align: center;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <header>
        <h1>Assistant Virtuel des Bibliothèques Paris-Saclay</h1>
        <p>Posez vos questions sur les bibliothèques de l'université</p>
    </header>
    
    <div class="chat-container" id="chatContainer">
        <div class="message bot-message">
            Bonjour ! Je suis l'assistant virtuel des bibliothèques de l'Université Paris-Saclay. 
            Comment puis-je vous aider aujourd'hui ?
        </div>
    </div>
    
    <div class="loading" id="loading">
        <p>Traitement de votre question...</p>
    </div>
    
    <div class="input-container">
        <input type="text" id="questionInput" placeholder="Posez votre question ici...">
        <button onclick="askQuestion()">Envoyer</button>
    </div>

    <script>
        // Permettre l'envoi de la question avec la touche Entrée
        document.getElementById('questionInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                askQuestion();
            }
        });

        function askQuestion() {
            const questionInput = document.getElementById('questionInput');
            const chatContainer = document.getElementById('chatContainer');
            const loading = document.getElementById('loading');
            
            const question = questionInput.value.trim();
            if (!question) return;
            
            // Ajouter le message de l'utilisateur
            const userMessage = document.createElement('div');
            userMessage.className = 'message user-message';
            userMessage.textContent = question;
            chatContainer.appendChild(userMessage);
            
            // Vider l'input et faire défiler vers le bas
            questionInput.value = '';
            chatContainer.scrollTop = chatContainer.scrollHeight;
            
            // Afficher l'indicateur de chargement
            loading.style.display = 'block';
            
            // Envoyer la question au serveur
            fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: question }),
            })
            .then(response => response.json())
            .then(data => {
                // Masquer l'indicateur de chargement
                loading.style.display = 'none';
                
                // Ajouter la réponse du bot
                const botMessage = document.createElement('div');
                botMessage.className = 'message bot-message';
                botMessage.textContent = data.answer;
                chatContainer.appendChild(botMessage);
                
                // Ajouter les sources si disponibles
                if (data.sources && data.sources.length > 0) {
                    const sourcesDiv = document.createElement('div');
                    sourcesDiv.className = 'sources';
                    sourcesDiv.innerHTML = '<strong>Sources:</strong> ';
                    
                    data.sources.forEach((source, index) => {
                        sourcesDiv.innerHTML += `${index > 0 ? ', ' : ''}${source.library} (${source.source})`;
                    });
                    
                    chatContainer.appendChild(sourcesDiv);
                }
                
                // Faire défiler vers le bas
                chatContainer.scrollTop = chatContainer.scrollHeight;
            })
            .catch(error => {
                console.error('Error:', error);
                loading.style.display = 'none';
                
                // Afficher un message d'erreur
                const errorMessage = document.createElement('div');
                errorMessage.className = 'message bot-message';
                errorMessage.textContent = "Désolé, une erreur s'est produite lors du traitement de votre question.";
                chatContainer.appendChild(errorMessage);
                
                chatContainer.scrollTop = chatContainer.scrollHeight;
            });
        }
    </script>
</body>
</html>""")

def initialize_bot():
    """Initialise le bot dans un thread séparé pour ne pas bloquer le démarrage de Flask."""
    global bot
    bot = BibliothequeRagBot()
    print("Bot initialisé et prêt à répondre aux questions.")

if __name__ == '__main__':
    # Créer les fichiers de template
    create_templates()
    
    # Initialiser le bot dans un thread séparé
    bot_thread = threading.Thread(target=initialize_bot)
    bot_thread.start()
    
    # Démarrer l'application Flask
    app.run(debug=True, host='0.0.0.0', port=5000)