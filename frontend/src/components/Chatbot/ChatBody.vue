<template>
  <div class="card-body card-chat-body" ref="pageChat">
    <div
      v-for="(message, index) in messages"
      :key="index"
      :class="message.role === 'user' ? 'user-message' : 'assistant-message'"
    >
      <div v-if="message.role === 'assistant'">
        <bot-message
          :ImageMessageBot="config.images.bot_image"
          :message="message"
          :baseApiUrl="baseApiUrl"
          :autoPlayAudio="shouldAutoPlay(message)"
        >
        </bot-message>
      </div>
      <div v-else-if="message.role === 'user'">
        <user-message
          :userProfilePic="config.images.user_profile_pic"
          :message="message"
        >
        </user-message>
      </div>
    </div>
    <typing-message
      v-if="userTranscribing"
      :profilePic="config.images.user_profile_pic"
      :message="config.transcribingMsg"
      :isBot="false"
    >
    </typing-message>
    <typing-message
      v-if="botTyping"
      :profilePic="config.images.bot_image"
      :message="getTypingMsg(botTypingMsg)"
      :isBot="true"
    >
    </typing-message>
  </div>
</template>

<script>
import BotMessage from "./BotMessage.vue";
import UserMessage from "./UserMessage.vue";
import TypingMessage from "./TypingMessage.vue";

export default {
  name: "ChatBody",
  props: {
    config: {
      type: Object,
      required: true,
    },
    messages: {
      type: Array,
      required: true,
    },
    userTranscribing: {
      type: Boolean,
      required: true,
    },
    botTyping: {
      type: Boolean,
      required: true,
    },
    botTypingMsg: {
      type: String,
      required: false,
      default: null,
    },
    baseApiUrl: {
      type: String,
      required: true,
    },
    handsFreeFlag: {
      type: Boolean,
      required: true,
    },
  },
  components: {
    BotMessage,
    UserMessage,
    TypingMessage,
  },
  methods: {
    getTypingMsg(msg) {
      if (msg == null) {
        return this.config.typingMsg;
      }
      return msg;
    },
    shouldAutoPlay(message) {
      return message.role === "assistant" && this.handsFreeFlag;
    },
  },
  watch: {
    messages(newMessages, oldMessages) {
      // Check if a new message has been added
      if (newMessages.length > oldMessages.length) {
        const newMessage = newMessages[newMessages.length - 1];
        // Check if the new message is from the assistant and if handsFreeFlag is true
        if (newMessage.role === "assistant" && this.handsFreeFlag) {
          // Find the BotMessage component for the new message and play its audio
          const botMessageComponent = this.$children.find(
              (component) =>
                  component.message === newMessage &&
                  component.$options.name === "BotMessage"
          );
          if (botMessageComponent) {
            botMessageComponent.playAudio();
          }
        }
      }
    },
  },
};
</script>

<style>
.card-chat-body {
  /* Add your styles here */
}

.user-message {
  /* Add styles for user messages */
}

.assistant-message {
  /* Add styles for assistant messages */
}
</style>
