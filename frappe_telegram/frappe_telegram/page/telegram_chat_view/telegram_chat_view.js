frappe.pages["telegram-chat-view"].on_page_load = function (wrapper) {
	const telegram_chat_view = new TelegramChatView(wrapper);
	$(wrapper).bind("show", () => {
		telegram_chat_view.showChatList();
	});
	window.telegram_chat_view = telegram_chat_view;
};

class TelegramChatView {
	chat_list = [];
	chat_list_offset = 0
	chat_list_limit_length = 20
	chat_list_has_more = true

	currentChat = null
	chat_messages = []
	chat_message_offset = 0
	chat_message_limit_length = 20
	chat_message_has_more = true

	constructor(wrapper) {
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: "Telegram Chat",
			single_column: true,
		});
		this.content = $(this.page.body);
	}

	async showChatList() {
		this.clearPage();
		await this.loadChatList()
		this.chat_list_wrapper = $(frappe.render_template("chat_list", {
			chat_list: this.chat_list
		})).appendTo(this.content)
		$(this.chat_list_wrapper).find(".chat-room").click((e) => {
			this.openChat($(e.currentTarget).data("chatId"));
		})
	}

	async loadChatList() {
		const r = await frappe.xcall(
			"frappe_telegram.frappe_telegram.page.telegram_chat_view.load_chat_rooms", {
			limit_start: this.chat_list_offset,
			limit_page_length: this.chat_list_limit_length
		}).catch(r => [])
		this.chat_list.push(...r);
		this.chat_list_offset += this.chat_list_limit_length
	}

	async loadChatMessages() {
		const r = await frappe.xcall(
			"frappe_telegram.frappe_telegram.page.telegram_chat_view.load_chat_messages", {
			chat_id: this.currentChat.chat_id,
			limit_start: this.chat_message_offset,
			limit_page_length: this.chat_message_limit_length
		}).catch(r => [])
		this.chat_messages.push(...r);
		this.chat_message_offset += this.chat_message_limit_length;
		return r;
	}

	clearPage() {
		$(this.content).empty();
	}

	async openChat(chat_id) {
		this.chat_message_offset = 0;
		this.currentChat = this.chat_list.find(x => x.chat_id == chat_id)
		this.chat_messages = []
		this.clearPage();

		await this.loadChatMessages()
		// debugger
		this.currentChatView = $(frappe.render_template("chat_view", { chat: this.currentChat })).appendTo(this.content);
		const messagesContainer = $(this.currentChatView).find(".chat-messages")

		let date = null;
		for (const msg of this.chat_messages) {
			if (date != moment(msg.creation).format("YYYY-MM-DD")) {
				date = moment(msg.creation).format("YYYY-MM-DD");
				$(frappe.render_template("chat_view_date_chip", { date: date })).appendTo(messagesContainer);
			}
			$(frappe.render_template("chat_message", { msg: msg })).appendTo(messagesContainer)
		}
	}
}
