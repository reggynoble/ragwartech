import { API_URL } from "./api.js";

export function initializeContact() {

  const form =
    document.querySelector("#contactForm");

  const status =
    document.querySelector("#formStatus");


  if (!form || !status) {
    return;
  }


  form.addEventListener(
    "submit",
    async event => {

      event.preventDefault();


      const name =
        document
          .querySelector("#name")
          .value
          .trim();


      const email =
        document
          .querySelector("#email")
          .value
          .trim();


      const message =
        document
          .querySelector("#message")
          .value
          .trim();


      if (!name || !email || !message) {

        status.textContent =
          "Please complete all fields.";

        return;
      }


      status.textContent =
        "Sending...";


      try {

        const response =
          await fetch(
            `${API_URL}/contact`,
            {
              method: "POST",

              headers: {
                "Content-Type":
                  "application/json"
              },

              body: JSON.stringify({
                name,
                email,
                message
              })
            }
          );


        if (!response.ok) {
          throw new Error(
            "Request failed"
          );
        }


        await response.json();


        status.textContent =
          "Message sent successfully.";

        form.reset();


      } catch (error) {

        console.error(error);

        status.textContent =
          "Unable to send message. Please try again.";

      }

    }
  );

}