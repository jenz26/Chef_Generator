# 🍽️ Chef Game - Generatore Menu Intelligente

Sistema completo per la generazione di menù personalizzati basati sui dati del gioco Chef. L'applicazione analizza le preferenze della clientela e crea menù ottimizzati con ricette, ingredienti, qualità e prezzi.

## ✨ Caratteristiche Principali

- **12 tipi di clientela** con preferenze reali dal gioco
- **447 ricette** organizzate per categoria (Antipasti, Portate Principali, Insalate, Zuppe, Contorni, Dessert)
- **Calcolo automatico dei prezzi** basato sui costi reali degli ingredienti
- **Sistema di compatibilità ingredienti** per ricette bilanciate
- **Analisi dettagliata** di ogni ricetta con ingredienti e qualità
- **Interface web intuitiva** con Streamlit

## 🎯 Funzionalità

### Generazione Menu Personalizzata
- Seleziona il tipo di clientela (Cheapskate, Gourmet, Families, ecc.)
- Il sistema genera automaticamente un menù ottimizzato
- Considera le preferenze alimentari e i budget della clientela

### Analisi Dettagliata
- **Costo totale del menù** e per singola ricetta
- **Qualità ingredienti** richiesta (Normal, First Choice, Gourmet)
- **Score di compatibilità** tra ingredienti
- **Profilo cliente** con preferenze visualizzate

### Categorie Menu Complete
- 🥗 **Antipasti** (69 ricette)
- 🍖 **Portate Principali** (192 ricette)
- 🥬 **Insalate** (24 ricette)
- 🍲 **Zuppe** (27 ricette)
- 🥔 **Contorni** (24 ricette)
- 🍰 **Dessert** (57 ricette)

## 🚀 Installazione e Uso

### Installazione Locale

```bash
# Clona la cartella o scarica i file
cd chef_menu_generator

# Installa le dipendenze
pip install -r requirements.txt

# Avvia l'applicazione
streamlit run app.py
```

### Deploy su Streamlit Cloud (Gratuito)

1. Carica tutti i file su GitHub
2. Vai su [streamlit.io](https://streamlit.io)
3. Collega il repository GitHub
4. L'app sarà disponibile online gratuitamente!

## 📊 Database Inclusi

### Customer Types (customer_types.json)
- **12 tipi di clientela** estratti dal gioco
- Preferenze alimentari, peso del prezzo, qualità richiesta
- Esempi: Cheapskate (economici), Gourmet (alta qualità), Vegetarian, Vegan

### Recipes Database (recipes_database.json)
- **447 ricette complete** con tutti i tier (1-3)
- Ingredienti, quantità, categoria (IMPORTANT/normale)
- Costi calcolati automaticamente
- Score di compatibilità ingredienti

### Ingredients Data (ingredients_data.json)
- **300+ ingredienti** con dati completi
- Costi per qualità (Normal, First Choice, Gourmet)
- Profili di sapore, calorie, tempo di cottura
- Tag per categorizzazione

### Ingredient Matches (matches_data.json)
- **13,563 compatibilità** tra ingredienti
- Valori da 1 a 3 (bassa, media, alta compatibilità)
- Usato per calcolare l'armonia delle ricette

## 🎮 Come Funziona l'Algoritmo

1. **Analisi Cliente**: Carica le preferenze del tipo di cliente selezionato
2. **Scoring Ricette**: Ogni ricetta riceve un punteggio basato su:
   - Preferenze alimentari del cliente (tag favoriti)
   - Rapporto qualità/prezzo
   - Compatibilità ingredienti
   - Valutazione base della ricetta
3. **Selezione Intelligente**: Seleziona le migliori ricette per ogni categoria
4. **Ottimizzazione Budget**: Rispetta i vincoli di budget del tipo di clientela

## 📈 Metriche Visualizzate

- **Costo totale menù** e per ricetta
- **Score di compatibilità** (1-5) per ogni ricetta
- **Tempo di preparazione** stimato
- **Distribuzione ricette** per categoria
- **Profilo radar** delle preferenze clientela
- **Analisi ingredienti** con costi dettagliati

## 🔧 Personalizzazioni Disponibili

- Budget massimo per ricetta
- Qualità minima ingredienti
- Filtri per restrizioni dietetiche
- Numero di ricette per categoria
- Visualizzazioni statistiche avanzate

## 📱 Streamlit Cloud Deploy

Per mettere online gratuitamente:

1. Crea un repository GitHub con tutti i file
2. Vai su [share.streamlit.io](https://share.streamlit.io)
3. Inserisci il link del repository
4. L'app sarà online in pochi minuti!

## 🎯 Perfetto per:

- **Giocatori di Chef** che vogliono ottimizzare i menù
- **Guide online** per il gioco
- **Tool di analisi** delle meccaniche di gioco
- **Generatori di contenuto** per video/stream

## 💡 Sviluppi Futuri

- Esportazione menù in PDF
- Confronto tra diversi tipi di clientela
- Simulazione profitti ristorante
- Integrazione con API del gioco (se disponibili)
- Modalità "sfida" con budget limitato

---

**Creato dai dati originali del gioco Chef per la community!** 🎮👨‍🍳