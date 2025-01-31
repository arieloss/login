document.addEventListener("DOMContentLoaded", () => {
    // Prévisualisation d'image avant l'envoi
    const imageInput = document.querySelector("#image");
    const imagePreview = document.createElement("img");
    imagePreview.style.maxWidth = "200px";
    imagePreview.style.display = "none";
    imageInput.parentNode.appendChild(imagePreview);

    imageInput.addEventListener("change", (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreview.src = e.target.result;
                imagePreview.style.display = "block";
            };
            reader.readAsDataURL(file);
        } else {
            imagePreview.style.display = "none";
        }
    });

    // Confirmation lors de l'ajout d'utilisateur
    const userForm = document.querySelector("form[action='/add-user']");
    userForm.addEventListener("submit", (event) => {
        const username = document.querySelector("#username").value;
        const confirmation = confirm(`Voulez-vous vraiment ajouter l'utilisateur ${username} ?`);
        if (!confirmation) {
            event.preventDefault();
        }
    });

    // Confirmation lors de la publication de contenu
    const publishForm = document.querySelector("form[action='/publish']");
    publishForm.addEventListener("submit", (event) => {
        const textContent = document.querySelector("#text").value.trim();
        if (!textContent) {
            alert("Le champ texte est vide. Veuillez ajouter du contenu.");
            event.preventDefault();
        } else {
            const confirmation = confirm("Voulez-vous vraiment publier ce contenu ?");
            if (!confirmation) {
                event.preventDefault();
            }
        }
    });

    // Gestion dynamique des statistiques
    const totalUsers = document.querySelector("#totalUsers");
    const totalPosts = document.querySelector("#totalPosts");
    const recentPosts = document.querySelector("#recentPosts");

    if (totalUsers && totalPosts && recentPosts) {
        // Exemple : Mise à jour simulée des statistiques toutes les 10 secondes
        setInterval(() => {
            totalUsers.textContent = parseInt(totalUsers.textContent) + 1;
            totalPosts.textContent = parseInt(totalPosts.textContent) + 1;
            recentPosts.textContent = parseInt(recentPosts.textContent) + 1;
        }, 10000);
    }

    // Gestion des messages reçus
    const messagesList = document.querySelector(".list-group");
    if (messagesList) {
        messagesList.addEventListener("click", (event) => {
            const target = event.target;
            if (target.tagName === "LI") {
                alert(`Message sélectionné : ${target.textContent}`);
            }
        });
    }
});
