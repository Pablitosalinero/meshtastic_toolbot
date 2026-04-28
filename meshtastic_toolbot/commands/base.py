class BaseCommand:
    def __init__(self, bot_config, db, interface):
        self.config = bot_config
        self.db = db
        self.interface = interface

    def handle(self, packet, channel_index, from_node, reply_to_id, text_args):
        raise NotImplementedError("Subclasses must implement handle()")
