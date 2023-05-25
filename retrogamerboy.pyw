
import os
import sys
import traceback
import configparser
import requests
import tkinter
import tkinter.ttk
import tkinter.font
import tkinter.filedialog
import tkinter.messagebox
import lib.sheets_client
import lib.utils
import time
import asyncio
import threading

from twitchio.ext import commands
from twitchio.ext import routines


class Bot(commands.Bot):

	def __init__(self, config):
		# Initialise our Bot with our access token, prefix and a list of channels to join on boot...
		super().__init__(token=config["TWITCH"]["ACCESS_TOKEN"], prefix='?', initial_channels=[config["TWITCH"]["CHANNEL"]])
		self.config = config

	async def event_ready(self):
		# We are logged in and ready to chat and use commands...
		print(f'Logged in as | {self.nick}')
		print(f'User id is | {self.user_id}')

	async def repeat_message_loop(self, message, period_in_seconds):
		while True:
			await self.get_channel(self.config["TWITCH"]["CHANNEL"]).send(message)
			await asyncio.sleep(period_in_seconds)
			
	def start_repeat_message_task(self, message, period_in_seconds):
		return self.loop.create_task(self.repeat_message_loop(message, period_in_seconds))
		
	def stop_repeat_message_task(self, task):
		task.cancel()
		
class BotThread(threading.Thread):
	def __init__(self, config):
		threading.Thread.__init__(self)
		self.daemon = True
		self.bot = Bot(config)

	def run(self):
		self.bot.run()
		
	def get_bot(self):
		return self.bot


class MainFrame(tkinter.Frame):
	TOKENS_FILENAME = "tokens.ini"
	
	def __init__(self, config, bot, window, **kwargs):
		tkinter.Frame.__init__(self, window, **kwargs)
		
		self.window = window
		
		default_font = tkinter.font.nametofont("TkDefaultFont")
		default_font.configure(size=12)
		self.window.option_add("*Font", default_font)
		
		self.model = None
		
		self.bot = bot
		self.config = config
		
		self.utils = lib.utils.Utils()
		
		self.pack(expand = tkinter.YES, fill = tkinter.BOTH)
		
		self.create_label(self, "Jeux: ", 0, 0)
		self.combo_games = self.create_combo(self, self.on_combo_games_changed, 0, 1)
		self.create_label(self, "Suffixe: ", 0, 2)
		self.entry_game_suffix = self.create_entry(self, "", True, 0, 3)
		self.create_label(self, "Fichier texte: ", 0, 4)
		self.entry_game_text_file = self.create_entry(self, "game.txt", True, 0, 5, 2)
		
		self.entry_support, self.entry_support_suffix, self.entry_support_text_file = self.create_line_controls(2, "Support: ", "support.txt")
		self.entry_content_type, self.entry_content_type_suffix, self.entry_content_type_text_file = self.create_line_controls(3, "Type de contenu: ", "content-type.txt")
		self.entry_specificity, self.entry_specificity_suffix, self.entry_specificity_text_file = self.create_line_controls(4, "Spécificité: ", "specificity.txt")
		self.entry_publisher, self.entry_publisher_suffix, self.entry_publisher_text_file = self.create_line_controls(5, "Editeur: ", "publisher.txt")
		self.entry_studio, self.entry_studio_suffix, self.entry_studio_text_file = self.create_line_controls(6, "Studio: ", "studio.txt")
		self.entry_link, self.entry_link_suffix, self.entry_link_text_file = self.create_line_controls(7, "Lien: ", "link.txt")
		self.entry_link_bot_button, self.entry_link_bot_prefix_text, self.entry_link_bot_period_text = self.add_bot_line_controls(8, self.on_bot_link_click)
		
		self.create_button(self, "Recharger Gdoc", self.on_reload_sheet_click, 9, 0, 7)
		self.create_button(self, "Envoyer vers les fichiers textes", self.on_send_to_text_click, 10, 0, 7)
		
	def create_line_controls(self, line, label, text_file_name):
		self.create_label(self, label, line, 0)
		entry = self.create_entry(self, "", False, line, 1)
		self.create_label(self, "Suffixe: ", line, 2)
		suffix = self.create_entry(self, "", True, line, 3)
		self.create_label(self, "Fichier texte: ", line, 4)
		text_file = self.create_entry(self, text_file_name, True, line, 5, 2)
		return entry, suffix, text_file
		
	def add_bot_line_controls(self, line, on_click_cb):
		self.create_label(self, "Préfixe: ", line, 2)
		prefix_text = self.create_entry(self, "", True, line, 3)
		self.create_label(self, "Période (sec): ", line, 4)
		period_text = self.create_entry(self, "300", True, line, 5, 1, 5)
		button = self.create_button(self, "Start repeat in chat", on_click_cb, line, 6, 1)
		return button, prefix_text, period_text
		
	def on_bot_link_click(self):
		if not hasattr(self, "bot_link_task") or self.bot_link_task is None:
			period_text = self.entry_link_bot_period_text.get()
			bot_text = self.entry_link_bot_prefix_text.get() + self.entry_link.get()
			if period_text != "" and bot_text != "":
				period = int(self.entry_link_bot_period_text.get())
				self.bot_link_task = self.bot.start_repeat_message_task(bot_text, period)
				self.entry_link_bot_button.config(text="Stop repeat in chat")
		else:
			self.stop_bot_link()
			
	def stop_bot_link(self):
		if hasattr(self, "bot_link_task") and self.bot_link_task is not None:
			self.bot.stop_repeat_message_task(self.bot_link_task)
			self.bot_link_task = None
			self.entry_link_bot_button.config(text="Start repeat in chat")
			
	def create_label(self, frame, text, row, column, columnspan=1):
		label = tkinter.Label(frame, text = text, anchor = tkinter.W)
		label.grid(sticky=tkinter.W, padx=2, pady=2, row=row, column=column, columnspan=columnspan)
		return label
		
	def create_combo(self, frame, on_changed_cb, row, column):
		combo = tkinter.ttk.Combobox(frame, state = "readonly")
		combo.grid(sticky=tkinter.W, padx=2, pady=2, row=row, column=column)
		combo.bind("<<ComboboxSelected>>", on_changed_cb)
		return combo
		
	def create_entry(self, frame, text, enabled, row, column, columnspan=1, width=23):
		if enabled:
			entry = tkinter.Entry(frame, width=width)
		else:
			entry = tkinter.Entry(frame, state="readonly", width=width)
		entry.grid(sticky=tkinter.W, padx=2, pady=2, row=row, column=column, columnspan=columnspan)
		self.set_entry_text(entry, text)
		return entry
		
	def create_button(self, frame, text, on_click_cb, row, column, columnspan):
		button = tkinter.Button(frame, relief = tkinter.GROOVE, text = text, command = on_click_cb)
		button.grid(sticky="EW", padx=2, pady=2, row=row, column=column, columnspan=columnspan)
		return button
		
	def set_entry_text(self, entry, text):
		disabled = entry["state"] == "readonly"
		
		if disabled:
			entry.configure(state=tkinter.NORMAL)
			
		entry.delete(0, tkinter.END)
		entry.insert(0, text)
		
		if disabled:
			entry.configure(state="readonly")
		
	def get_combo_value(self, combo):
		current_index = combo.current()
		values = combo.cget("values")
		if current_index >= 0 and current_index < len(values):
			return values[current_index]
		return ""
		
	def select_combo_value(self, combo, value):
		values = combo.cget("values")
		
		i = 0
		for v in values:
			if v == value:
				combo.current(i)
				return True
			i += 1
			
		return False
		
	def on_reload_sheet_click(self):
		self.reload_sheet()
		
	def append_text_to_list(self, l, text, suffix):
		if text != "":
			l.append(text + suffix)
		return l
		
	def on_send_to_text_click(self):
		text_file_to_text = {}
		
		text_file_to_text[self.entry_game_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_game_text_file.get(), []), self.combo_games.cget("values")[self.combo_games.current()], self.entry_game_suffix.get())
		text_file_to_text[self.entry_support_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_support_text_file.get(), []), self.entry_support.get(), self.entry_support_suffix.get())
		text_file_to_text[self.entry_content_type_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_content_type_text_file.get(), []), self.entry_content_type.get(), self.entry_content_type_suffix.get())
		text_file_to_text[self.entry_specificity_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_specificity_text_file.get(), []), self.entry_specificity.get(), self.entry_specificity_suffix.get())
		text_file_to_text[self.entry_publisher_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_publisher_text_file.get(), []), self.entry_publisher.get(), self.entry_publisher_suffix.get())
		text_file_to_text[self.entry_studio_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_studio_text_file.get(), []), self.entry_studio.get(), self.entry_studio_suffix.get())
		text_file_to_text[self.entry_link_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_link_text_file.get(), []), self.entry_link.get(), self.entry_link_suffix.get())
		
		for k, v in text_file_to_text.items():
			if k != "":
				self.utils.write_file("wb", "text-files/" + k, "".join(v))
		
	def on_combo_games_changed(self, event):
		self.process_on_combo_games_changed(None)
		
	def fill_games(self, init_values):
		values = []
		
		for value in self.model["games"]:
			values.append(value)
		
		self.combo_games.config(values = values)
		if len(values) > 0:
			self.combo_games.current(0)
		
		if init_values and ("game" in init_values):
			self.select_combo_value(self.combo_games, init_values["game"])
			
		self.process_on_combo_games_changed(init_values)
		
	def process_on_combo_games_changed(self, init_values):
		current_game = self.get_combo_value(self.combo_games)
		
		if current_game != self.model["current_game"]:
			self.model["current_game"] = current_game
			
			model_game = self.model["games"][current_game]
			
			self.stop_bot_link()
			
			self.set_entry_text(self.entry_support, model_game["support"])
			self.set_entry_text(self.entry_content_type, model_game["content_type"])
			self.set_entry_text(self.entry_specificity, model_game["specificity"])
			self.set_entry_text(self.entry_publisher, model_game["publisher"])
			self.set_entry_text(self.entry_studio, model_game["studio"])
			self.set_entry_text(self.entry_link, model_game["link"])
			
	def set_sheet_data_simple_values_to_model(self, data, start_row, row_id_to_game, model, field_name):
		row_id = start_row
		
		if "rowData" not in data:
			return
			
		for row_data in data["rowData"]:
			if row_id in row_id_to_game:
				if "values" in row_data and "formattedValue" in row_data["values"][0]:
					model["games"][row_id_to_game[row_id]][field_name] = row_data["values"][0]["formattedValue"].strip()
			row_id += 1
			
	def build_model(self):
		model = {
			"current_game": "",
			"games": {},
		}
		
		config_sheet = self.config["SHEET"]
		
		response = self.sheets_client.get_sheets()
		
		first_line = config_sheet["FIRST_GAME_LINE"]
		
		ranges = []
		
		worksheet_name = "RetroGamerBoy"
		
		ranges.append(worksheet_name + "!" + config_sheet["GAME_COLUMN"] + first_line + ":" + config_sheet["GAME_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["SUPPORT_COLUMN"] + first_line + ":" + config_sheet["SUPPORT_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["CONTENT_TYPE_COLUMN"] + first_line + ":" + config_sheet["CONTENT_TYPE_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["SPECIFICITY_COLUMN"] + first_line + ":" + config_sheet["SPECIFICITY_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["PUBLISHER_COLUMN"] + first_line + ":" + config_sheet["PUBLISHER_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["STUDIO_COLUMN"] + first_line + ":" + config_sheet["STUDIO_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["LINK_COLUMN"] + first_line + ":" + config_sheet["LINK_COLUMN"])
			
		values = self.sheets_client.get_values(ranges)
		
		sheets = values["sheets"]
		
		for sheet in sheets:
			if "data" in sheet:
				data = sheet["data"]
				
				row_id_to_game = {}
				
				# Game column
				for d in data:
					column_id = d.get("startColumn", 0)
					if column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["GAME_COLUMN"]):
						row_id = d.get("startRow", 0)
						
						for r in d["rowData"]:
							if "values" in r and "formattedValue" in r["values"][0]:
								game_name = r["values"][0]["formattedValue"]
								
								model["games"][game_name] = {
									"support": "",
									"content_type": "",
									"specificity": "",
									"publisher": "",
									"studio": "",
									"link": "",
								}
								row_id_to_game[row_id] = game_name
								
							row_id += 1
							
						break
						
				for d in data:
					column_id = d.get("startColumn", 0)
					start_row = d.get("startRow", 0)
						
					if column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["SUPPORT_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "support")
					elif column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["CONTENT_TYPE_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "content_type")
					elif column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["SPECIFICITY_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "specificity")
					elif column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["PUBLISHER_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "publisher")
					elif column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["STUDIO_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "studio")
					elif column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["LINK_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "link")
						
		return model
		
	def load(self):
		if not os.path.isfile(MainFrame.TOKENS_FILENAME):
			tkinter.messagebox.showerror("Error", " File "+ MainFrame.TOKENS_FILENAME +" not found. Please run grant_permissions.bat.")
			sys.exit()
			
		st = time.time()
		self.sheets_client = lib.sheets_client.SheetsClient(self.config["SHEET"]["GDOC_API_KEY"], self.config["SHEET"]["OAUTH_CLIENT_ID"], self.config["SHEET"]["OAUTH_CLIENT_SECRET"], self.config["SHEET"]["SPREAD_SHEET_ID"], MainFrame.TOKENS_FILENAME)
		print(time.time(), "load sheets_client init (ms): ", (time.time() - st) * 1000)
		
		st = time.time()
		self.model = self.build_model()
		print(time.time(), "load build_model (ms): ", (time.time() - st) * 1000)
		
		st = time.time()
		init_values = self.load_context("context.sav")
		print(time.time(), "load load_context (ms): ", (time.time() - st) * 1000)
		
		self.fill_games(init_values)
		st = time.time()
		print(time.time(), "load fill_games (ms): ", (time.time() - st) * 1000)
		
	def reload_sheet(self):
		init_values = {}
		init_values["game"] = self.model["current_game"]
		
		self.model = self.build_model()
		self.fill_games(init_values)
		
	def load_context(self, file_name):
		init_values = {}
		if os.path.exists(file_name):
			config = configparser.ConfigParser()
			config.read(file_name)
			
			if "game" in config["CONTEXT"]:
				init_values["game"] = config["CONTEXT"]["game"].replace("<SPACE>", " ")
				
			if "game_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_game_suffix, config["CONTEXT"]["game_suffix"].replace("<SPACE>", " "))
			if "game_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_game_text_file, config["CONTEXT"]["game_text_file"].replace("<SPACE>", " "))
				
			if "support_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_support_suffix, config["CONTEXT"]["support_suffix"].replace("<SPACE>", " "))
			if "support_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_support_text_file, config["CONTEXT"]["support_text_file"].replace("<SPACE>", " "))
				
			if "content_type_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_content_type_suffix, config["CONTEXT"]["content_type_suffix"].replace("<SPACE>", " "))
			if "content_type_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_content_type_text_file, config["CONTEXT"]["content_type_text_file"].replace("<SPACE>", " "))
				
			if "specificity_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_specificity_suffix, config["CONTEXT"]["specificity_suffix"].replace("<SPACE>", " "))
			if "specificity_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_specificity_text_file, config["CONTEXT"]["specificity_text_file"].replace("<SPACE>", " "))
				
			if "publisher_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_publisher_suffix, config["CONTEXT"]["publisher_suffix"].replace("<SPACE>", " "))
			if "publisher_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_publisher_text_file, config["CONTEXT"]["publisher_text_file"].replace("<SPACE>", " "))
				
			if "studio_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_studio_suffix, config["CONTEXT"]["studio_suffix"].replace("<SPACE>", " "))
			if "studio_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_studio_text_file, config["CONTEXT"]["studio_text_file"].replace("<SPACE>", " "))
				
			if "link_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_link_suffix, config["CONTEXT"]["link_suffix"].replace("<SPACE>", " "))
			if "link_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_link_text_file, config["CONTEXT"]["link_text_file"].replace("<SPACE>", " "))
			if "link_bot_prefix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_link_bot_prefix_text, config["CONTEXT"]["link_bot_prefix"].replace("<SPACE>", " "))
			if "link_bot_period" in config["CONTEXT"]:
				self.set_entry_text(self.entry_link_bot_period_text, config["CONTEXT"]["link_bot_period"].replace("<SPACE>", " "))
				
		return init_values
		
	def save_context(self, file_name):
		config = configparser.ConfigParser()
		
		config["CONTEXT"] = {
			"game": self.model["current_game"].replace(" ", "<SPACE>"),
			"game_suffix": self.entry_game_suffix.get().replace(" ", "<SPACE>"),
			"game_text_file": self.entry_game_text_file.get().replace(" ", "<SPACE>"),
			"support_suffix": self.entry_support_suffix.get().replace(" ", "<SPACE>"),
			"support_text_file": self.entry_support_text_file.get().replace(" ", "<SPACE>"),
			"content_type_suffix": self.entry_content_type_suffix.get().replace(" ", "<SPACE>"),
			"content_type_text_file": self.entry_content_type_text_file.get().replace(" ", "<SPACE>"),
			"specificity_suffix": self.entry_specificity_suffix.get().replace(" ", "<SPACE>"),
			"specificity_text_file": self.entry_specificity_text_file.get().replace(" ", "<SPACE>"),
			"publisher_suffix": self.entry_publisher_suffix.get().replace(" ", "<SPACE>"),
			"publisher_text_file": self.entry_publisher_text_file.get().replace(" ", "<SPACE>"),
			"studio_suffix": self.entry_studio_suffix.get().replace(" ", "<SPACE>"),
			"studio_text_file": self.entry_studio_text_file.get().replace(" ", "<SPACE>"),
			"link_suffix": self.entry_link_suffix.get().replace(" ", "<SPACE>"),
			"link_text_file": self.entry_link_text_file.get().replace(" ", "<SPACE>"),
			"link_bot_prefix": self.entry_link_bot_prefix_text.get().replace(" ", "<SPACE>"),
			"link_bot_period": self.entry_link_bot_period_text.get().replace(" ", "<SPACE>"),
		}
		
		with open(file_name, "w") as f:
			config.write(f)
		
	def on_close(self):
		self.save_context("context.sav")
		try:
			self.window.destroy()
		except:
			pass
			
def main():
	config = configparser.ConfigParser()
	config.read("config.ini")
	
	bot_thread = BotThread(config)
	bot_thread.start()
	
	window = tkinter.Tk()
	window.title("RetroGameBoy")
	window.resizable(False, False)
	f = MainFrame(config, bot_thread.get_bot(), window)
	window.protocol("WM_DELETE_WINDOW", f.on_close)
	window.after(1, f.load)
	window.mainloop()
	

class Logger(object):
	def __init__(self, filename = "logs.txt"):
		self.terminal = sys.stdout
		self.log = open(filename, "w")
		
	def write(self, message):
		self.terminal.write(message)
		self.log.write(message)
		self.log.flush()
		
	def flush(self):
		self.terminal.flush()
		self.log.flush()
		
if __name__ == "__main__":
	logger = Logger()
	sys.stdout = logger
	sys.stderr = logger
	main()
	