# gui.py complet
from tkinter import *
from tkinter import scrolledtext, font as tkfont
from chatbot import DisasterChatbot

class ChatbotGUI:
    def __init__(self, master):
        self.master = master
        self.chatbot = DisasterChatbot()
        master.title("Chatbot d'Urgence")
        master.geometry("600x500")
        master.configure(bg="#f0f2f5")
        
        # Widgets
        self.create_widgets()
        self.display_message("Système", "Assistant d'urgence prêt. Posez vos questions sur les catastrophes naturelles.", True)

    def create_widgets(self):
        # Zone de chat
        self.chat_area = scrolledtext.ScrolledText(
            self.master, wrap=WORD, state=DISABLED,
            font=("Helvetica", 10), padx=10, pady=10
        )
        self.chat_area.pack(expand=True, fill=BOTH, padx=10, pady=5)
        
        # Zone de saisie
        input_frame = Frame(self.master, bg="#f0f2f5")
        input_frame.pack(padx=10, pady=10, fill=X)
        
        self.user_input = Entry(input_frame, font=("Helvetica", 10))
        self.user_input.pack(side=LEFT, expand=True, fill=X)
        self.user_input.bind("<Return>", lambda e: self.send_message())
        
        Button(input_frame, text="Envoyer", command=self.send_message,
              bg="#4CAF50", fg="white").pack(side=RIGHT)

    def send_message(self):
        user_text = self.user_input.get().strip()
        if not user_text:
            return
            
        self.display_message("Vous", user_text, False)
        self.user_input.delete(0, END)
        
        try:
            response = self.chatbot.generate_response(user_text)
            self.display_message("Assistant", response, True)
        except Exception as e:
            self.display_message("Erreur", f"Problème avec le chatbot: {str(e)}", True)

    def display_message(self, sender, message, is_bot):
        self.chat_area.config(state=NORMAL)
        bg = "#E3F2FD" if is_bot else "#F5F5F5"
        self.chat_area.tag_config(sender, background=bg, lmargin1=10, rmargin=10)
        self.chat_area.insert(END, f"{sender}:\n", ("bold", sender))
        self.chat_area.insert(END, f"{message}\n\n", sender)
        self.chat_area.config(state=DISABLED)
        self.chat_area.see(END)