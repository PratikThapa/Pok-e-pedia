import tkinter as tk
from tkinter import messagebox, ttk
import requests
import io
from PIL import Image, ImageTk
import json
import time
import os
from logic import fetch_evolution_data, fetch_pokemon_data, fetch_species_data

class PokedexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pok-e-pedia")
        self.root.geometry("800x900")
        self.root.configure(bg='#2C3E50')

        # Add Pokeball image
        self.pokeball_image = Image.open("image\\pokeball.png")
        self.pokeball_image = self.pokeball_image.resize((100, 100), Image.LANCZOS)
        self.pokeball_photo = ImageTk.PhotoImage(self.pokeball_image)
        self.pokeball_label = tk.Label(self.root, image=self.pokeball_photo, bg='#2C3E50')
        self.pokeball_label.pack(pady=10)

        self.current_data = None
        self.team = []
        self.favorites = []
        self.animation_frames = None
        self.animation_index = 0
        self.animation_job = None

        self.search_history = []  # Store the history of Pokémon searched
        self.max_history = 5  # Limit to the last 5 searches

        self.create_widgets()

    def create_widgets(self):
        # Search box
        self.entry = tk.Entry(self.root, font=('Arial', 14), width=20)
        self.entry.pack(pady=10, padx=20)
        self.entry.bind("<FocusIn>", self.show_search_history)
        self.search_button = tk.Button(self.root, text="Search", command=self.search_pokemon)
        self.search_button.pack(pady=10)

        # History listbox (hidden initially)
        self.history_listbox = tk.Listbox(self.root, font=('Arial', 12), height=5)
        self.history_listbox.pack(pady=5, padx=20)
        self.history_listbox.bind("<Double-1>", self.select_from_history)
        self.history_listbox.pack_forget()  # Hide it initially

        self.tab_control = ttk.Notebook(self.root)
        self.info_tab = ttk.Frame(self.tab_control)
        self.evolution_tab = ttk.Frame(self.tab_control)
        self.moves_tab = ttk.Frame(self.tab_control)
        self.team_tab = ttk.Frame(self.tab_control)
        self.favorites_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.info_tab, text='Info')
        self.tab_control.add(self.evolution_tab, text='Evolution')
        self.tab_control.add(self.moves_tab, text='Moves')
        self.tab_control.add(self.team_tab, text='Team Builder')
        self.tab_control.add(self.favorites_tab, text='Favorites')
        self.tab_control.pack(expand=1, fill='both')

        self.create_info_tab()
        self.create_evolution_tab()
        self.create_moves_tab()
        self.create_team_tab()
        self.create_favorites_tab()

    def show_search_history(self, event=None):
        # Show the search history when the user focuses on the search box
        self.history_listbox.delete(0, tk.END)
        if self.search_history:
            for pokemon in self.search_history:
                self.history_listbox.insert(tk.END, pokemon.capitalize())
            self.history_listbox.pack(pady=5, padx=20)
        else:
            self.history_listbox.pack_forget()

    def search_pokemon(self):
        # Cancel ongoing animation
        if self.animation_job:
            self.root.after_cancel(self.animation_job)

        pokemon_name = self.entry.get().lower()

        # Avoid searching empty strings
        if pokemon_name.strip() == "":
            return

        data = fetch_pokemon_data(pokemon_name)

        if data:
            # Update search history
            if pokemon_name not in self.search_history:
                self.search_history.insert(0, pokemon_name)
                if len(self.search_history) > self.max_history:
                    self.search_history.pop()  # Remove oldest history if exceeding max limit

            # Hide search history after selection
            self.history_listbox.pack_forget()

            self.display_pokemon(data)
            evolution_data = fetch_evolution_data(data['species_url'])
            if evolution_data:
                self.display_evolution_line(evolution_data['chain'])
                self.display_evolution_methods(evolution_data['chain'])
            else:
                messagebox.showwarning("Warning", "No evolution data found.")
            self.display_moves(data['moves'])
        else:
            messagebox.showerror("Error", f"Pokémon '{pokemon_name}' not found.")

    def select_from_history(self, event):
        # Select a Pokémon from the search history
        selected_pokemon = self.history_listbox.get(self.history_listbox.curselection())
        self.entry.delete(0, tk.END)
        self.entry.insert(0, selected_pokemon.lower())
        self.search_pokemon()

    def display_evolution_methods(self, evolution_chain):
        # This function will extract and display evolution methods from the evolution chain
        evolution_methods = []

        # Ensure evolution_chain is a dictionary and not empty
        if not isinstance(evolution_chain, dict):
            print("Invalid evolution chain data")
            return

        while evolution_chain:
            species = evolution_chain.get('species', {})
            species_name = species.get('name', 'Unknown')

            # Extracting the evolution method
            evolution_details = evolution_chain.get('evolution_details', [])

            if evolution_details:
                # Check for triggers such as level-up, use of items, or other evolution methods
                for detail in evolution_details:
                    method = detail.get('trigger', {}).get('name', 'Unknown')  # Trigger method (e.g., level-up)
                    item = detail.get('item', {}).get('name', None)  # Item required for evolution

                    if item:
                        # If an item is required for evolution, display it
                        evolution_methods.append(f"{species_name} evolves by using {item.replace('-', ' ').title()}.")
                    elif method and method != 'Unknown':
                        # If a method is available, display it (e.g., level-up, trade)
                        evolution_methods.append(f"{species_name} evolves by {method.replace('-', ' ').title()}.")
                    else:
                        # If no method is known, just mention that the evolution method is unknown
                        evolution_methods.append(f"{species_name} evolves.")

            else:
                # If no detailed evolution method, just mention the evolution chain
                evolution_methods.append(f"{species_name} evolves.")

            # Move to the next Pokémon in the evolution chain
            # If there are multiple evolutions, loop through each `evolves_to`
            evolution_chain = evolution_chain.get('evolves_to', [None])[0]

        # Display the evolution methods in the Evolution tab
        for widget in self.evolution_tab.winfo_children():
            widget.destroy()  # Clear the previous content in the Evolution tab

        title_label = tk.Label(self.evolution_tab, text="Evolution Methods:", font=('Arial', 16, 'bold'), bg='#2C3E50', fg='white')
        title_label.pack(pady=10)

        if evolution_methods:
            for method in evolution_methods:
                method_label = tk.Label(self.evolution_tab, text=method, font=('Arial', 12), bg='#2C3E50', fg='white')
                method_label.pack(pady=5)
        else:
            no_method_label = tk.Label(self.evolution_tab, text="No evolution data available.", font=('Arial', 12), bg='#2C3E50', fg='white')
            no_method_label.pack(pady=10)


    def search_pokemon(self):
        pokemon_name = self.entry.get().lower()

        if pokemon_name.strip() == "":
            return

        data = fetch_pokemon_data(pokemon_name)

        if data:
            # Fetch evolution data
            evolution_data = fetch_evolution_data(data['species_url'])
            if evolution_data:
                self.display_evolution_line(evolution_data['chain'])  # For evolutionary line (optional)
                self.display_evolution_methods(evolution_data['chain'])  # This now shows methods of evolution
            else:
                messagebox.showwarning("Warning", "No evolution data found.")
            self.display_moves(data['moves'])  # Display moves as before
        else:
            messagebox.showerror("Error", f"Pokémon '{pokemon_name}' not found.")

    def select_from_history(self, event):
        # Select a Pokémon from the search history
        selected_pokemon = self.history_listbox.get(self.history_listbox.curselection())
        self.entry.delete(0, tk.END)
        self.entry.insert(0, selected_pokemon.lower())
        self.search_pokemon()

    def create_widgets(self):
        self.entry = tk.Entry(self.root, font=('Arial', 14), width=20)
        self.entry.pack(pady=10, padx=20)
        self.search_button = tk.Button(self.root, text="Search", command=self.search_pokemon)
        self.search_button.pack(pady=10)

        self.tab_control = ttk.Notebook(self.root)
        self.info_tab = ttk.Frame(self.tab_control)
        self.evolution_tab = ttk.Frame(self.tab_control)
        self.moves_tab = ttk.Frame(self.tab_control)
        self.team_tab = ttk.Frame(self.tab_control)
        self.favorites_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.info_tab, text='Info')
        self.tab_control.add(self.evolution_tab, text='Evolution')
        self.tab_control.add(self.moves_tab, text='Moves')
        self.tab_control.add(self.team_tab, text='Team Builder')
        self.tab_control.add(self.favorites_tab, text='Favorites')
        self.tab_control.pack(expand=1, fill='both')

        self.create_info_tab()
        self.create_evolution_tab()
        self.create_moves_tab()
        self.create_team_tab()
        self.create_favorites_tab()

    def create_info_tab(self):
        self.name_label = tk.Label(self.info_tab, text="", font=('Arial', 22))
        self.name_label.pack()
        self.type_label = tk.Label(self.info_tab, text="")
        self.type_label.pack()
        self.weight_label = tk.Label(self.info_tab, text="")
        self.weight_label.pack()
        self.height_label = tk.Label(self.info_tab, text="")
        self.height_label.pack()
        self.lore_label = tk.Label(self.info_tab, text="", wraplength=500, justify="left")
        self.lore_label.pack(pady=10)
        self.image_label = tk.Label(self.info_tab)
        self.image_label.pack()
        self.add_to_team_button = tk.Button(self.info_tab, text="Add to Team", command=self.add_to_team)
        self.add_to_team_button.pack(pady=10)
        self.add_to_favorites_button = tk.Button(self.info_tab, text="Add to Favorites", command=self.add_to_favorites)
        self.add_to_favorites_button.pack(pady=10)

    def create_evolution_tab(self):
        self.evolution_inner_frame = tk.Frame(self.evolution_tab)
        self.evolution_inner_frame.pack(fill=tk.BOTH, expand=True)

    def create_moves_tab(self):
        self.moves_inner_frame = tk.Frame(self.moves_tab)
        self.moves_inner_frame.pack(fill=tk.BOTH, expand=True)

    def create_team_tab(self):
        team_frame = tk.Frame(self.team_tab)
        team_frame.pack(fill=tk.BOTH, expand=True)
        
        self.team_listbox = tk.Listbox(team_frame, font=('Arial', 14), height=15)
        self.team_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.clear_team_button = tk.Button(self.team_tab, text="Clear Team", command=self.clear_team)
        self.clear_team_button.pack(pady=10)

    def create_favorites_tab(self):
        favorites_frame = tk.Frame(self.favorites_tab)
        favorites_frame.pack(fill=tk.BOTH, expand=True)
        
        self.favorites_listbox = tk.Listbox(favorites_frame, font=('Arial', 14), height=15)
        self.favorites_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.clear_favorites_button = tk.Button(self.favorites_tab, text="Clear Favorites", command=self.clear_favorites)
        self.clear_favorites_button.pack(pady=10)
        
    def search_pokemon(self):
        # Cancel ongoing animation
        if self.animation_job:
            self.root.after_cancel(self.animation_job)

        pokemon_name = self.entry.get()
        data = fetch_pokemon_data(pokemon_name)

        if data:
            self.display_pokemon(data)
            evolution_data = fetch_evolution_data(data['species_url'])
            if evolution_data:
                self.display_evolution_line(evolution_data['chain'])
            else:
                messagebox.showwarning("Warning", "No evolution data found.")
            self.display_moves(data['moves'])
        else:
            messagebox.showerror("Error", f"Pokémon '{pokemon_name}' not found.")

    def display_pokemon(self, data):
        self.current_data = data
        self.name_label.config(text=data['name'].capitalize())
        self.type_label.config(text=f"Type: {', '.join(data['types']).capitalize()}")
        self.weight_label.config(text=f"Weight: {data['weight']} kg")
        self.height_label.config(text=f"Height: {data['height']} m")
        species_data = fetch_species_data(data['species_url'])
        if species_data:
            self.lore_label.config(text=species_data.get('flavor_text_entries', [{}])[0].get('flavor_text', '').replace('\n', ' '))
        self.display_image(data['sprites']['front_default'], animated_url=data['sprites'].get('versions', {}).get('generation-v', {}).get('black-white', {}).get('animated', {}).get('front_default'))

    def display_image(self, image_url, animated_url=None):
        try:
            if animated_url:  # Display animated sprite
                response = requests.get(animated_url)
                response.raise_for_status()
                img_data = io.BytesIO(response.content)
                self.animation_frames = Image.open(img_data)
                self.animation_index = 0
                self.animate_sprite()
            else:
                # Display static image
                response = requests.get(image_url)
                response.raise_for_status()
                img_data = response.content
                image = Image.open(io.BytesIO(img_data))
                image = image.resize((150, 150), Image.LANCZOS)
                self.photo = ImageTk.PhotoImage(image)
                self.image_label.config(image=self.photo)
                self.image_label.image = self.photo
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def animate_sprite(self):
        if self.animation_frames:
            try:
                frame = ImageTk.PhotoImage(self.animation_frames.copy().convert('RGBA'))
                self.photo = frame
                self.image_label.config(image=self.photo)
                self.image_label.image = self.photo
                self.animation_index = (self.animation_index + 1) % self.animation_frames.n_frames
                self.animation_frames.seek(self.animation_index)
                self.animation_job = self.root.after(100, self.animate_sprite)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to animate sprite: {e}")


    def display_evolution_line(self, chain):
        # Clear previous widgets
        for widget in self.evolution_inner_frame.winfo_children():
            widget.destroy()

        # List to store the evolution details
        evolution_steps = []

        # Create a canvas and a scrollbar for the evolution details
        canvas = tk.Canvas(self.evolution_inner_frame)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self.evolution_inner_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)

        # Create a frame inside the canvas to hold the evolution details
        evolution_frame = tk.Frame(canvas, bg='#34495E')
        canvas.create_window((0, 0), window=evolution_frame, anchor="nw")

        def display_recursive(chain):
            species_name = chain['species']['name']
            evolution_data = fetch_pokemon_data(species_name)

            if evolution_data:
                frame = tk.Frame(evolution_frame, bg='#34495E')
                frame.pack(pady=10, fill=tk.BOTH)

                label = tk.Label(frame, text=species_name.capitalize(), font=('Arial', 14), bg='#34495E', fg='white')
                label.pack(side=tk.TOP, padx=5, pady=5)

                try:
                    # Attempt to fetch sprite
                    sprite_url = evolution_data['sprites']['front_default']
                    img_response = requests.get(sprite_url)
                    img_response.raise_for_status()
                    img_data = io.BytesIO(img_response.content)
                    img = Image.open(img_data).resize((150, 150), Image.LANCZOS)
                    sprite = ImageTk.PhotoImage(img)
                    sprite_label = tk.Label(frame, image=sprite, bg='#34495E')
                    sprite_label.image = sprite
                    sprite_label.pack(side=tk.RIGHT)
                except Exception as e:
                    print(f"Failed to load evolution sprite: {e}")

                # Handle evolution details
                evolution_details = chain.get('evolution_details', [])
                if evolution_details:
                    evolution_detail = evolution_details[0]
                    if evolution_detail:
                        # Safely check if the 'item' exists in evolution detail
                        evolution_method = evolution_detail.get('trigger', {}).get('name', 'Unknown')
                        evolution_item = evolution_detail.get('item', None)

                        if evolution_item:
                            evolution_item = evolution_item.get('name', 'Unknown Item')
                        else:
                            evolution_item = None

                        # Handling triggers and items
                        if evolution_method == 'level-up':
                            evolution_method = 'Level Up'
                        elif evolution_method == 'use-item' and evolution_item:
                            evolution_method = f"Use Item: {evolution_item.replace('-', ' ').capitalize()}"
                        elif evolution_method == 'use-move':
                            evolution_method = 'Use Move'
                        else:
                            evolution_method = 'Unknown Evolution Method'
                    else:
                        evolution_method = 'No Evolution Method Available'
                        evolution_item = None
                else:
                    evolution_method = 'No Evolution Method Available'
                    evolution_item = None

                method_label = tk.Label(frame, text=f"Evolution Method: {evolution_method}", font=('Arial', 10), bg='#34495E', fg='white')
                method_label.pack(side=tk.TOP, padx=5, pady=5)

                # Store the evolution details in the list
                evolution_steps.append({
                    'species': species_name.capitalize(),
                    'method': evolution_method,
                    'sprite_url': sprite_url if 'sprite_url' in locals() else None
                })

            # Recursively process each 'evolves_to' entry
            if 'evolves_to' in chain:
                for next_evolution in chain.get('evolves_to', []):
                    display_recursive(next_evolution)

        # Start the recursion
        display_recursive(chain)

        # Update the scroll region of the canvas to include all the children of the evolution_frame
        evolution_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

        # Return the evolution steps
        return evolution_steps

    def display_moves(self, moves):
        for widget in self.moves_inner_frame.winfo_children():
            widget.destroy()
        moves_label = tk.Label(self.moves_inner_frame, text="Moves:", font=('Arial', 14, 'bold'), bg='#34495E', fg='white')
        moves_label.pack(pady=(10, 0))
        competitive_moves = ["stealth-rock", "earthquake", "recover", "toxic", "spikes", "calm-mind", "defog"]  # Example competitive moves
        for move in moves[:15]:  # Show first 15 moves
            move_label = tk.Label(self.moves_inner_frame, text=move.capitalize() + (" (Competitive)" if move in competitive_moves else ""), bg='#34495E', fg='#FFFFFF')
            move_label.pack(anchor='w', padx=10, pady=2)

    from tkinter import messagebox

    def add_to_team(self):
        if self.current_data is None:
            messagebox.showerror("Error", "No Pokémon selected.")
            return
        
        pokemon_name = self.current_data['name'].lower()
        
        if pokemon_name in self.team:
            messagebox.showwarning("Already in Team", f"{pokemon_name.capitalize()} is already in your team.")
        else:
            self.team.append(pokemon_name)
            messagebox.showinfo("Added to Team", f"{pokemon_name.capitalize()} has been added to your team.")
            self.update_team_tab()
            
    def clear_team(self):
        self.team = []
        self.update_team_tab()

    def update_team_tab(self):
        self.team_listbox.delete(0, tk.END)
        for member in self.team:
            self.team_listbox.insert(tk.END, member.capitalize())

    def add_to_favorites(self):
        if self.current_data is None:
        # Handle the case where current_data is not set or is None
            messagebox.showerror("Error", "No Pokémon selected.")
            return

        # Now you can safely access self.current_data['name']
        if 'name' in self.current_data:
            # Check if the Pokémon is already in favorites
            if self.current_data['name'] in self.favorites:
                messagebox.showwarning("Already in Favorites", f"{self.current_data['name'].capitalize()} is already in your favorites.")
            else:
                self.favorites.append(self.current_data['name'])
                messagebox.showinfo("Added to Favorites", f"{self.current_data['name'].capitalize()} has been added to your favorites.")
                self.update_favorites_tab()
        else:   
            messagebox.showwarning("No Name Found", "Current Pokémon does not have a name.")

    def clear_favorites(self):
        self.favorites = []
        self.update_favorites_tab()

    def update_favorites_tab(self):
        self.favorites_listbox.delete(0, tk.END)
        for fav in self.favorites:
            self.favorites_listbox.insert(tk.END, fav.capitalize())

if __name__ == "__main__":
    root = tk.Tk()
    app = PokedexApp(root)
    root.mainloop()