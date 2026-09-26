import { API_URL } from "./api.js";

export function initializeAIChat() {

  const form =
    document.querySelector("#chatForm");

  const input =
    document.querySelector("#chatInput");

  const messages =
    document.querySelector("#chatMessages");


  if (!form || !input || !messages) {
    return;
  }


  form.addEventListener(
    "submit",
    async event => {

      event.preventDefault();


      const message =
        input.value.trim();


      if (!message) {
        return;
      }


      addMessage(
        "user",
        message
      );


      input.value = "";

      input.disabled = true;


      const submitButton =
        form.querySelector("button");

      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent =
          "Thinking...";
      }


      const loading =
        addMessage(
          "assistant",
          "Thinking..."
        );


      try {

        const response =
          await fetch(
            `${API_URL}/chat`,
            {
              method: "POST",

              headers: {
                "Content-Type":
                  "application/json"
              },

              body: JSON.stringify({
                message
              })
            }
          );


        if (!response.ok) {

          throw new Error(
            `AI request failed: ${response.status}`
          );

        }


        const data =
          await response.json();


        loading.remove();


        addMessage(
          "assistant",
          data.response,
          data.sources || []
        );


      } catch (error) {

        console.error(
          "AI chat error:",
          error
        );


        loading.remove();


        addMessage(
          "assistant",
          "Sorry, the AI service is currently unavailable."
        );


      } finally {

        input.disabled = false;


        if (submitButton) {

          submitButton.disabled = false;

          submitButton.textContent =
            "Ask";

        }


        input.focus();

      }

    }
  );


  function addMessage(
    role,
    text,
    sources = []
  ) {

    const message =
      document.createElement("div");


    message.className =
      `chat-message ${role}`;


    const label =
      document.createElement("span");


    label.className =
      "chat-label";


    label.textContent =
      role === "user"
        ? "YOU"
        : "AI";


    const paragraph =
      document.createElement("p");


    paragraph.textContent =
      text;


    message.append(
      label,
      paragraph
    );


    // ========================================
    // ASSISTANT ACTIONS
    // ========================================

    if (role === "assistant") {

      const actions =
        document.createElement("div");


      actions.className =
        "chat-actions";


      const copyButton =
        document.createElement("button");


      copyButton.type =
        "button";


      copyButton.className =
        "chat-copy";


      copyButton.textContent =
        "Copy";


      copyButton.addEventListener(
        "click",
        async () => {

          try {

            await navigator.clipboard.writeText(
              text
            );


            copyButton.textContent =
              "Copied!";


            setTimeout(() => {

              copyButton.textContent =
                "Copy";

            }, 1500);


          } catch (error) {

            console.error(
              "Copy failed:",
              error
            );


            copyButton.textContent =
              "Copy failed";


            setTimeout(() => {

              copyButton.textContent =
                "Copy";

            }, 1500);

          }

        }
      );


      actions.append(
        copyButton
      );


      message.append(
        actions
      );

    }


    // ========================================
    // SOURCES
    // ========================================

    if (
      role === "assistant" &&
      sources.length > 0
    ) {

      const sourceContainer =
        document.createElement("div");


      sourceContainer.className =
        "chat-sources";


      const sourceLabel =
        document.createElement("span");


      sourceLabel.className =
        "chat-source-label";


      sourceLabel.textContent =
        "Sources:";


      sourceContainer.append(
        sourceLabel
      );


      sources.forEach(
        source => {

          const sourceItem =
            document.createElement("span");


          sourceItem.className =
            "chat-source";


          sourceItem.textContent =
            source;


          sourceContainer.append(
            sourceItem
          );

        }
      );


      message.append(
        sourceContainer
      );

    }


    messages.appendChild(
      message
    );


    messages.scrollTop =
      messages.scrollHeight;


    return message;

  }

}