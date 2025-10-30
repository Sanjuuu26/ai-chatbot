import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, END
from PIL import Image, ImageTk
import sqlite3
import openai
import hashlib
import secrets
import numpy as np

# -------------------- CONFIG --------------------
openai.api_key = os.getenv("OPENAI_API_KEY")  # Use environment variable
DB_NAME = "chatbot.db"

# -------------------- PASSWORD HASHING --------------------
def hash_password(password):
    """Hash a password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${password_hash}"

def verify_password(password, stored_hash):
    """Verify a password against stored hash"""
    try:
        salt, stored_password_hash = stored_hash.split('$')
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return password_hash == stored_password_hash
    except:
        return False

# -------------------- DATABASE SETUP --------------------
def setup_database():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS register (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fname TEXT NOT NULL,
                lname TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                securityQ TEXT NOT NULL,
                securityA TEXT NOT NULL
            )
        """)
        
        conn.commit()
        print("Database ready!")
        
    except sqlite3.Error as err:
        print(f"Database Error: {err}")
    finally:
        if conn:
            conn.close()

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_NAME)
        return conn
    except sqlite3.Error as err:
        messagebox.showerror("Database Error", f"Cannot connect to database: {err}")
        return None

# -------------------- CHATBOT RESPONSES --------------------
def get_chatbot_response(user_input):
    """Get response from OpenAI or fallback to predefined responses"""
    
    # First try OpenAI
    try:
        if openai.api_key and openai.api_key != "your_openai_api_key_here":
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful and friendly AI assistant. Provide clear, concise, and helpful responses."},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=300,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI Error: {e}")
        # Fall through to predefined responses
    
    # Predefined responses for common questions
    user_input_lower = user_input.lower()
    
    # Greetings
    if any(word in user_input_lower for word in ['hello', 'hi', 'hey', 'hola']):
        return "Hello! 👋 How can I assist you today?"
    
    # How are you
    elif any(phrase in user_input_lower for phrase in ['how are you', 'how do you do']):
        return "I'm doing great! Thanks for asking. I'm here and ready to help you with anything you need! 😊"
    
    # Name questions
    elif any(phrase in user_input_lower for phrase in ['what is your name', 'who are you', 'your name']):
        return "I'm your friendly AI chatbot! I'm here to help answer your questions and chat with you! 🤖"
    
    # Capabilities
    elif any(phrase in user_input_lower for phrase in ['what can you do', 'help', 'capabilities']):
        return "I can help you with:\n• Answering questions\n• Having conversations\n• Providing information\n• Chatting about various topics\nJust ask me anything! 💡"
    
    # Time questions
    elif any(phrase in user_input_lower for phrase in ['time', 'what time', 'current time']):
        from datetime import datetime
        current_time = datetime.now().strftime("%I:%M %p")
        return f"The current time is {current_time} ⏰"
    
    # Date questions
    elif any(phrase in user_input_lower for phrase in ['date', 'today', 'what date']):
        from datetime import datetime
        current_date = datetime.now().strftime("%B %d, %Y")
        return f"Today is {current_date} 📅"
    
    # Weather
    elif any(phrase in user_input_lower for phrase in ['weather', 'temperature', 'forecast']):
        return "I'd love to give you weather information, but I need access to current weather data. You might want to check a weather app or website for accurate forecasts! ☀️🌧️"
    
    # Math questions
    elif any(phrase in user_input_lower for phrase in ['calculate', 'math', 'add', 'subtract', 'multiply', 'divide']):
        try:
            if '+' in user_input or '-' in user_input or '*' in user_input or '/' in user_input:
                result = eval(''.join([c for c in user_input if c in '0123456789+-*/.() ']))
                return f"The answer is: {result} 🧮"
        except:
            return "I can help with basic math! Try asking something like 'What is 15 + 27?' or 'Calculate 100 divided by 4'"
    
    # Goodbye
    elif any(phrase in user_input_lower for phrase in ['bye', 'goodbye', 'see you', 'exit', 'quit']):
        return "Goodbye! 👋 It was nice chatting with you. Feel free to come back anytime!"
    
    # Thank you
    elif any(phrase in user_input_lower for phrase in ['thank', 'thanks']):
        return "You're welcome! 😊 I'm glad I could help. Is there anything else you'd like to know?"
    
    # Jokes
    elif any(phrase in user_input_lower for phrase in ['joke', 'funny', 'make me laugh']):
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything! 🤓",
            "Why did the scarecrow win an award? He was outstanding in his field! 🌾",
            "Why don't eggs tell jokes? They'd crack each other up! 🥚",
            "What do you call a fake noodle? An impasta! 🍝"
        ]
        import random
        return random.choice(jokes)
    
    # Default response for unknown queries
    else:
        responses = [
            "That's an interesting question! I'm here to help and learn. 🤔",
            "I'm not sure I understand completely. Could you rephrase that? 💭",
            "That's a great question! Let me think about how to best answer that. 🧠",
            "I'm here to chat and help! Could you tell me more about what you're looking for? 💬",
            "I'm constantly learning new things. Could you ask me in a different way? 📚"
        ]
        import random
        return random.choice(responses)

# -------------------- CHATBOT WINDOW --------------------
class ChatbotWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Chatbot")
        self.geometry("1550x800")
        self.configure(bg="darkred")
        
        # Create the chat log and text box
        self.chatlog = scrolledtext.ScrolledText(self, font=("Arial", 14), wrap="word", state="disabled")
        self.chatlog.configure(bg="blue", fg="white")
        self.chatlog.place(relx=0.025, rely=0.025, relheight=0.75, relwidth=0.95)

        self.textbox = tk.Entry(self, font=("Arial", 14), bd=2, relief="flat", bg="lightblue", fg="black")
        self.textbox.place(relx=0.025, rely=0.8, relheight=0.1, relwidth=0.8)
        self.textbox.bind("<Return>", lambda event: self.on_send_button_click())

        self.send_button = tk.Button(self, text="Send", font=("Arial", 12), bg="black", fg="white", 
                                   relief="groove", bd=2, command=self.on_send_button_click)
        self.send_button.place(relx=0.85, rely=0.8, relheight=0.1, relwidth=0.125)
        
        # Add welcome message
        self.chatlog.configure(state="normal")
        self.chatlog.insert(END, "🤖 Bot: Welcome! I'm your AI assistant. How can I help you today?\n\n")
        self.chatlog.insert(END, "You can ask me about:\n")
        self.chatlog.insert(END, "• General knowledge and information\n")
        self.chatlog.insert(END, "• Help with questions and problems\n") 
        self.chatlog.insert(END, "• Casual conversation\n")
        self.chatlog.insert(END, "• Calculations and facts\n")
        self.chatlog.insert(END, "• And much more!\n\n")
        self.chatlog.insert(END, "Just type your message and press Enter or click Send! 🚀\n\n")
        self.chatlog.configure(state="disabled")
        
        self.textbox.focus()

    def on_send_button_click(self):
        user_input = self.textbox.get().strip()
        self.textbox.delete(0, END)

        if not user_input:
            self.chatlog.configure(state="normal")
            self.chatlog.insert(END, "⚠️ Please enter a valid input.\n\n")
            self.chatlog.configure(state="disabled")
            return

        # Display user message
        self.chatlog.configure(state="normal")
        self.chatlog.insert(END, f"👤 You: {user_input}\n")
        self.chatlog.configure(state="disabled")
        
        # Disable button while processing
        self.send_button.config(state="disabled", text="Thinking...")
        self.update_idletasks()

        # Get bot response
        bot_response = get_chatbot_response(user_input)
        
        # Display bot response
        self.chatlog.configure(state="normal")
        self.chatlog.insert(END, f"🤖 Bot: {bot_response}\n\n")
        self.chatlog.configure(state="disabled")
        self.chatlog.see(END)
        
        # Re-enable button
        self.send_button.config(state="normal", text="Send")

# -------------------- LOGIN WINDOW --------------------
class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Login System")
        self.root.geometry("1550x800")
        self.root.configure(bg="#f0f0f0")

        # Background image
        try:
            BASE_DIR = os.path.dirname(__file__)
            photo_dir = os.path.join(BASE_DIR, "photo")
            self.bg_image_path = os.path.join(photo_dir, "vvv.jpg")
            
            bg_img = Image.open(self.bg_image_path).resize((1550, 800))
            self.bg = ImageTk.PhotoImage(bg_img)
            tk.Label(self.root, image=self.bg).place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print(f"Background image error: {e}")
            tk.Label(self.root, bg="lightblue").place(x=0, y=0, relwidth=1, relheight=1)

        # Login frame
        frame = tk.Frame(self.root, bg="#ffffff", bd=2, relief="ridge")
        frame.place(relx=0.5, rely=0.5, anchor="center", width=350, height=450)

        tk.Label(frame, text="Get Started", font=("Arial", 22, "bold"), fg="#333333", bg="#ffffff").pack(pady=20)

        tk.Label(frame, text="Username", font=("Arial", 14), fg="#333333", bg="#ffffff").pack(pady=(10,0))
        self.txtuser = ttk.Entry(frame, font=("Arial", 14))
        self.txtuser.pack(pady=5, ipady=5, ipadx=5, fill="x", padx=40)

        tk.Label(frame, text="Password", font=("Arial", 14), fg="#333333", bg="#ffffff").pack(pady=(10,0))
        self.txtpass = ttk.Entry(frame, font=("Arial", 14), show="*")
        self.txtpass.pack(pady=5, ipady=5, ipadx=5, fill="x", padx=40)
        self.txtpass.bind('<Return>', lambda event: self.login())

        login_btn = tk.Button(frame, text="Login", command=self.login, font=("Arial", 14, "bold"),
                            fg="white", bg="#1a73e8", bd=0)
        login_btn.pack(pady=20, ipadx=10, ipady=5)

        register_btn = tk.Button(frame, text="New User Register", command=self.register_window,
                               font=("Arial", 12, "bold"), fg="white", bg="#f57c00", bd=0)
        register_btn.pack(pady=5, ipadx=10, ipady=5)

        forgot_btn = tk.Button(frame, text="Forgot Password", command=self.forgot_password_window,
                             font=("Arial", 12, "bold"), fg="white", bg="#388e3c", bd=0)
        forgot_btn.pack(pady=5, ipadx=10, ipady=5)

    def login(self):
        if self.txtuser.get() == "" or self.txtpass.get() == "":
            messagebox.showerror("Error", "All fields required")
            return
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM register WHERE email=? AND password=?", 
                             (self.txtuser.get(), self.txtpass.get()))
                row = cursor.fetchone()
                
                if row:
                    messagebox.showinfo("Success", f"Welcome {self.txtuser.get()}!")
                    self.open_chatbot()
                else:
                    messagebox.showerror("Error", "Invalid Username or Password")
                    
            except sqlite3.Error as err:
                messagebox.showerror("Database Error", f"{err}")
            finally:
                conn.close()

    def open_chatbot(self):
        self.root.withdraw()
        chatbot_window = ChatbotWindow(self.root)
        chatbot_window.protocol("WM_DELETE_WINDOW", lambda: self.on_chatbot_close(chatbot_window))

    def on_chatbot_close(self, chatbot_window):
        chatbot_window.destroy()
        self.root.deiconify()
        self.txtuser.delete(0, END)
        self.txtpass.delete(0, END)
        self.txtuser.focus()

    def register_window(self):
        RegisterWindow(self.root)

    def forgot_password_window(self):
        if self.txtuser.get() == "":
            messagebox.showerror("Error", "Please enter username to reset password")
        else:
            ForgotPasswordWindow(self.root, self.txtuser.get())

# -------------------- REGISTER WINDOW --------------------
class RegisterWindow:
    def __init__(self, master):
        self.top = tk.Toplevel(master)
        self.top.title("Register")
        self.top.geometry("800x650")
        self.top.configure(bg="#ffffff")
        self.top.grab_set()

        self.var_fname = tk.StringVar()
        self.var_lname = tk.StringVar()
        self.var_email = tk.StringVar()
        self.var_password = tk.StringVar()
        self.var_confpass = tk.StringVar()
        self.var_securityQ = tk.StringVar()
        self.var_securityA = tk.StringVar()

        tk.Label(self.top, text="REGISTER HERE", font=("Arial", 25, "bold"), fg="#1b5e20", bg="#ffffff").pack(pady=20)

        self.create_label_entry("First Name", self.var_fname, 50, 100)
        self.create_label_entry("Last Name", self.var_lname, 400, 100)
        self.create_label_entry("Email", self.var_email, 50, 160)
        self.create_label_entry("Password", self.var_password, 400, 160, show="*")
        self.create_label_entry("Confirm Password", self.var_confpass, 50, 220, show="*")

        tk.Label(self.top, text="Select Security Question", font=("Arial", 14), bg="#ffffff").place(x=400, y=220)
        self.combo_security_Q = ttk.Combobox(self.top, textvariable=self.var_securityQ, font=("Arial", 14), state="readonly")
        self.combo_security_Q["values"] = ("Select", "Your Birth Place", "Your Mother Name", "Your Pet Name")
        self.combo_security_Q.place(x=400, y=250, width=250)
        self.combo_security_Q.current(0)

        self.create_label_entry("Security Answer", self.var_securityA, 50, 280)

        tk.Button(self.top, text="Register", command=self.register_user, font=("Arial", 15, "bold"),
                 fg="white", bg="#1b5e20").place(x=300, y=350, width=150, height=40)

    def create_label_entry(self, text, variable, x, y, show=None):
        tk.Label(self.top, text=text, font=("Arial", 14), bg="#ffffff").place(x=x, y=y)
        tk.Entry(self.top, textvariable=variable, font=("Arial", 14), show=show).place(x=x, y=y+30, width=250, height=30)

    def register_user(self):
        if self.var_password.get() != self.var_confpass.get():
            messagebox.showerror("Error", "Passwords do not match")
            return
            
        if not all([self.var_fname.get(), self.var_lname.get(), self.var_email.get(), self.var_password.get()]):
            messagebox.showerror("Error", "All fields are required")
            return

        # Hash the password before storing
        hashed_password = hash_password(self.var_password.get())

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO register (fname,lname,email,password,securityQ,securityA) VALUES (?,?,?,?,?,?)",
                             (self.var_fname.get(), self.var_lname.get(), self.var_email.get(), 
                              hashed_password, self.var_securityQ.get(), self.var_securityA.get()))
                conn.commit()
                messagebox.showinfo("Success", "Registration Successful!")
                self.top.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Email already exists!")
            except sqlite3.Error as err:
                messagebox.showerror("Error", f"{err}")
            finally:
                conn.close()

# -------------------- FORGOT PASSWORD WINDOW --------------------
class ForgotPasswordWindow:
    def __init__(self, master, email):
        self.top = tk.Toplevel(master)
        self.top.title("Forgot Password")
        self.top.geometry("400x400")
        self.top.configure(bg="#ffffff")
        self.top.grab_set()
        self.email = email

        tk.Label(self.top, text="Select Security Question", font=("Arial", 14), bg="#ffffff").pack(pady=10)
        self.combo_security_Q = ttk.Combobox(self.top, font=("Arial", 14), state="readonly")
        self.combo_security_Q["values"] = ("Select", "Your Birth Place", "Your Mother Name", "Your Pet Name")
        self.combo_security_Q.pack(pady=5)
        self.combo_security_Q.current(0)

        tk.Label(self.top, text="Security Answer", font=("Arial", 14), bg="#ffffff").pack(pady=10)
        self.txt_security = ttk.Entry(self.top, font=("Arial", 14))
        self.txt_security.pack(pady=5)

        tk.Label(self.top, text="New Password", font=("Arial", 14), bg="#ffffff").pack(pady=10)
        self.txt_newpass = ttk.Entry(self.top, font=("Arial", 14), show="*")
        self.txt_newpass.pack(pady=5)

        tk.Button(self.top, text="Reset Password", command=self.reset_pass, font=("Arial", 14, "bold"),
                 fg="white", bg="#1b5e20").pack(pady=20)

    def reset_pass(self):
        if self.combo_security_Q.get() == "Select" or not self.txt_security.get() or not self.txt_newpass.get():
            messagebox.showerror("Error", "All fields are required")
            return

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM register WHERE email=? AND securityQ=? AND securityA=?",
                             (self.email, self.combo_security_Q.get(), self.txt_security.get()))
                row = cursor.fetchone()
                if row:
                    # Hash the new password before storing
                    hashed_password = hash_password(self.txt_newpass.get())
                    cursor.execute("UPDATE register SET password=? WHERE email=?", (hashed_password, self.email))
                    conn.commit()
                    messagebox.showinfo("Success", "Password reset successful!")
                    self.top.destroy()
                else:
                    messagebox.showerror("Error", "Incorrect security answer or question")
            except sqlite3.Error as err:
                messagebox.showerror("Database Error", f"{err}")
            finally:
                conn.close()

# -------------------- MAIN --------------------
if __name__ == "__main__":
    setup_database()
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()