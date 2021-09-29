## Frappe Telegram

Telegram Bot Manager for Frappe. This is a wrapper around [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) tuned for frappe. Please go through the documentations of `python-telegram-bot` to easily customize your bot.

### Features
- ✅ Frappe Context for each incoming Updates
- ✅ Multi Bot support
- ✅ Runs the bot independently from the web server process
- ✅ Custom Bot implementations via Hooks
- ✅ Frappe User Login
- ✅ Frappe User signup
- ✅ Tracks Chats and contained messages
- ✅ Supports sending messages from bot via frappe hooks / controller methods
- ⏳ Integration with frappe `Notification` doctype

### DocTypes
- `Telegram Bot`  
Add all your telegram-bots here with their `api-tokens`
- `Telegram User`  
Any telegram-user that interacts with your bot comes here. Authentication is when `Telegram User` is linked to frappe's `User`
- `Telegram Chat`  
All private chats, groups where the bot gets notified comes here
- `Telegram Message`  
All messages - incoming & outgoing gets logged here

### Page
- `Telegram Chat View`  
A simple chat-page within frappe just for your telegram-bots

### Guides
- [Basic Setup](./docs/basic_setup.md)
- [User Authentication](./docs/auth.md)
- [Running in DEV mode](./docs/dev_setup.md)
- [Supported Hooks for Customization](./docs/hooks.md)
- [Setting up for Production](./docs/production.md)
- [Meta Conversation Driver](./docs/meta_conversation_driver.md)
- ⏳ Example: Login Notifier
- ⏳ Example: Activity Notifier

#### License

MIT