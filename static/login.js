// Sélection du formulaire et des éléments nécessaires
const loginForm = document.getElementById('loginForm');
const errorMessage = document.getElementById('errorMessage');

// Événement de soumission du formulaire
loginForm.addEventListener('submit', (event) => {
    event.preventDefault(); // Empêche l'envoi par défaut du formulaire

    // Récupération des valeurs saisies
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();

    // Validation des champs
    if (!username || !password) {
        errorMessage.textContent = 'Tous les champs doivent être remplis.';
        errorMessage.style.display = 'block';
        return;
    }

    // Simulation de l'envoi des données
    const loginData = {
        username: username,
        password: password
    };

    console.log('Données envoyées:', loginData);

    // Simulation de vérification (à remplacer par un appel API réel)
    if (username === 'admin' && password === '1234') {
        alert('Connexion réussie!');
        window.location.href = '/dashboard'; // Redirection après connexion réussie
    } else {
        errorMessage.textContent = 'Nom d’utilisateur ou mot de passe incorrect.';
        errorMessage.style.display = 'block';
    }
});
