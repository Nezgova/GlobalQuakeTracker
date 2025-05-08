# main.py
"""
Point d'entrée principal - Aucun changement nécessaire
"""
from gui import ChatbotGUI
import tkinter as tk

def main():
    root = tk.Tk()
    app = ChatbotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()