<template>
  <nav-bar :shopping-cart="shoppingCart" @open-cart="openCart"></nav-bar>
  <shopping-cart
    v-if="isCartOpen"
    ref="shoppingCart"
    :shopping-cart="shoppingCart"
    @close-cart="closeCart"
    @clear-shopping-cart="clearCart"
    @remove-from-cart="removeFromCart"
    @registerAction="registerAction"
  >
  </shopping-cart>

  <div>
    <div class="row justify-content-center">
      <div>
        <div class="app-container">
          <restaurants-container
            ref="restaurantsContainer"
            @add-to-cart="addToCart"
            @register-action="registerAction"
          >
          </restaurants-container>
          <chat-container
            ref="chatContainer"
            :isChatOpen="isChatOpen"
            :config="config"
            :messages="messages"
            :isRecordingFlag="isRecordingFlag"
            :recordedVoiceURL="recordedVoiceURL"
            :timeRecorded="timeRecorded"
            :botTyping="botTyping"
            :botTypingMsg="botTypingMsg"
            :userTranscribing="userTranscribing"
            :handsFreeFlag="handsFreeFlag"
            @send-message="sendMessage"
            @toggle-recording="toggleRecording"
            @cancel-audio="cancelAudio"
            @toggle-chatbot="toggleChatBot"
            @toggle-handsfree="toggleHandsFree"
          >
          </chat-container>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import NavBar from "./NavBar/NavBar.vue";
import ShoppingCart from "./ShoppingCart/ShoppingCart.vue";
import ChatContainer from "./Chatbot/ChatContainer.vue";
import RestaurantsContainer from "./Restaurants/RestaurantsContainer.vue";
import "./styles/common.css";
import config from "./general_config.json";
import axios from "axios";

export default {
  name: "AppContainer",
  components: {
    NavBar,
    ShoppingCart,
    ChatContainer,
    RestaurantsContainer,
  },
  data() {
    return {
      // Init
      config,
      isCartOpen: false,
      shoppingCart: [],
      baseApiUrl: "http://127.0.0.1:8080/", // Sửa lại URL và cổng
      handsFreeFlag: false,

      // Chatbot
      isChatOpen: false,
      messages: [
        {
          role: "assistant",
          content: config.fstMsg,
        },
      ],

      // User performed actions logger
      actions: [],

      // Audio
      isRecordingFlag: false,
      recordedVoiceURL: null,
      lastestAudioBlob: null,
      timeRecorded: 0,

      // Typing
      botTyping: false,
      botTypingMsg: null,
      userTranscribing: false,
    };
  },
  methods: {
    // -- Shopping Cart --
    openCart() {
      let flag_register_new_action = true;
      if (this.isCartOpen) {
        flag_register_new_action = false;
      }

      this.isCartOpen = true;
      // registering action
      if (flag_register_new_action) {
        this.registerAction("the shopping cart was opened");
      }
    },
    closeCart() {
      let flag_register_new_action = true;
      if (!this.isCartOpen) {
        flag_register_new_action = false;
      }
      this.isCartOpen = false;
      // registering action
      if (flag_register_new_action) {
        this.registerAction("the shopping cart was closed");
      }
    },
    clearCart() {
      this.shoppingCart.forEach((foodItem) => {
        foodItem.fadeAway = true;
        setTimeout(() => {
          this.shoppingCart = this.shoppingCart.filter(
              (item) => item !== foodItem
          );
        }, 200); // Remove the item after 0.2 seconds (200 milliseconds)
        foodItem.fadeAway = false;
      });
      this.registerAction(
          "removed all items from the shopping cart, it is now empty"
      );
    },
    addToCart(foodItem) {
      // Should check if the foodItem name is already in the cart
      // If so, increment the quantity

      if (this.shoppingCart.length === 0) {
        this.shoppingCart.push(foodItem);
        // registering action
        this.registerAction(foodItem.name + " was added to the shopping cart");
      } else {
        const index = this.shoppingCart.findIndex(
            (item) => item.name === foodItem.name
        );
        if (index === -1) {
          this.shoppingCart.push(foodItem);
          // registering action
          this.registerAction(
              foodItem.name + " was added to the shopping cart"
          );
        } else {
          this.shoppingCart[index].quantity += 1;
          // registering action
          this.registerAction(
              this.shoppingCart[index].name +
              " was added again to the shopping cart, totalizing " +
              this.shoppingCart[index].quantity +
              " items"
          );
        }
      }
      // console.log(this.shoppingCart)
    },
    removeFromCart(foodItem) {
      const index = this.shoppingCart.findIndex(
          (item) => item.id === foodItem.id
      );
      this.shoppingCart[index].fadeAway = true;
      // registering action
      this.registerAction(
          this.shoppingCart[index].name +
          " was removed completely from the shopping cart"
      );

      setTimeout(() => {
        this.shoppingCart[index].fadeAway = false;
        this.shoppingCart.splice(index, 1);
      }, 200); // Remove the item after the animation duration
    },

    // -- Messages management --

    // Chatbot
    toggleChatBot() {
      this.isChatOpen = !this.isChatOpen;
    },
    // Handsfree
    toggleHandsFree() {
      this.handsFreeFlag = !this.handsFreeFlag;
      console.log("Handsfree toggled: " + this.handsFreeFlag);
    },
    // Messages handling
    async sendMessage(textMessage) {
      /*Sends message to backend*/

      // If there's a new audio
      if (this.recordedVoiceURL !== null) {
        try {
          textMessage = await this.sendAudio(this.lastestAudioBlob);
          console.log(textMessage);
        } catch (error) {
          console.log(error);
          return;
        }
      }

      // Checking for empty string
      if (textMessage) {
        if (!textMessage.trim() && !this.recordedVoiceURL) {
          return;
        }
      }

      // Thêm tin nhắn người dùng vào mảng messages
      this.messages.push({
        role: "user",
        content: textMessage,
      });

      // Scrolling down
      this.scrollDown();

      // Gọi API run_query
      await this.generateAnswer(textMessage);
    },
    async generateAnswer(textMessage) {
      // Message backend interaction
      this.botTyping = true;

      try {
        const response = await axios.post(
            `${this.baseApiUrl}run_query`,
            {
              user_input: textMessage,
            },
            {
              headers: {
                "Content-Type": "application/json",
              },
            }
        );

        console.log(response);
        let answer = response.data["result"];

        console.log(answer);
        this.botTypingMsg = null;

        this.messages.push({
          role: "assistant",
          content: answer,
        });

        this.botTyping = false;
        this.scrollDown();

        if (answer === "Rejected" || answer === "Approved") {
        this.isCartOpen = true;
        }
      } catch (error) {
        console.log(error);
        this.messages.push({
          role: "assistant",
          content:
              "<span style='color:red;'>Error:</span> Please try again later.<br/> Description: " +
              error,
        });
        this.botTyping = false;
      }
    },

    // Utils
    getCurrentTime() {
      const today = new Date();
      let hourTime = today.getHours();
      let minuteTime = today.getMinutes();
      let secondTime = today.getSeconds();
      let currentTime = hourTime + ":" + minuteTime + ":" + secondTime;
      return currentTime;
    },
    scrollDown() {
      this.$nextTick(() => {
        const chatMessages =
            this.$refs.chatContainer.$refs.chatBody.$refs.pageChat;
        if (chatMessages) {
          chatMessages.scrollTop = chatMessages.scrollHeight;
        }
      });
    },
    registerAction(msg) {
      this.actions.push("@action:" + msg + " at " + this.getCurrentTime());
      console.log(this.actions);
    },

    // Audio
    sendAudio(blob) {
      try {
        this.userTranscribing = true;
        this.scrollDown();
        const fileReader = new FileReader();
        fileReader.readAsDataURL(blob);
        return new Promise((resolve, reject) => {
          fileReader.onloadend = async () => {
            const base64String = fileReader.result.replace(
                /^data:(.*;base64,)?/,
                ""
            );
            try {
              const response = await axios.post(
                  `${this.baseApiUrl}transcribe`,
                  {audio: base64String}
              );
              this.userTranscribing = false;
              this.recordedVoiceURL = null;
              resolve(response.data.response);
            } catch (error) {
              reject(error);
              this.userTranscribing = false;
            }
          };
        });
      } catch (error) {
        console.error("Error sending audio:", error);
        this.userTranscribing = false;
        return Promise.reject(error);
      }
    },

    // Audio Manipulation
    toggleRecording() {
      this.isRecordingFlag = !this.isRecordingFlag;
      if (this.isRecordingFlag) {
        this.chunks = [];
        this.recordedVoiceURL = null; // clear previous recording
        navigator.mediaDevices.getUserMedia({audio: true}).then((stream) => {
          this.recorder = new MediaRecorder(stream);
          this.recorder.addEventListener("dataavailable", (event) => {
            this.chunks.push(event.data);
          });
          this.recorder.addEventListener("stop", () => {
            this.lastestAudioBlob = new Blob(this.chunks, {
              type: "audio/mp3; codecs=opus",
            });
            this.recordedVoiceURL = URL.createObjectURL(this.lastestAudioBlob); // set recorded audio URL
          });
          this.recorder.start();
          this.timerInterval = setInterval(() => {
            this.timeRecorded += 10;
          }, 10);
        });
      } else {
        clearInterval(this.timerInterval);
        this.timeRecorded = 0;
        this.recorder.stop();
      }
    },
    cancelAudio() {
      this.isRecordingFlag = false;
      this.recordedVoiceURL = null;
    },
  },
};
</script>

<style>
.app-container {
  padding: 20px;
}
</style>
