# Hooks & Customizations
There are mainly 3 hooks available:
- `telegram_bot_handler`  
This gets invoked with params `telegram_bot` & `updater`

- `telegram_update_pre_processors`  
These gets invoked before each and every incoming updates. This should be a list of cmds to methods that accepts `update` & `context`, similar to every other handlers you could attach to the bot.

- `telegram_update_post_processors`  
These gets invoked after all the update handlers are executed.
