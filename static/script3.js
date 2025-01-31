document.addEventListener("DOMContentLoaded", () => {
    setInterval(fetchPresences, 5000); // Mise à jour toutes les 5 secondes
    fetchPresences();
});

async function fetchPresences() {
    try {
        const response = await fetch("http://192.168.100.6:8000/api/presences");
        if (!response.ok) {
            throw new Error("Erreur lors de la récupération des données");
        }
        const data = await response.json();
        populateTable(data);
    } catch (error) {
        console.error("Erreur:", error);
    }
}

function populateTable(presences) {
    const tableBody = document.getElementById("studentsTable");
    tableBody.innerHTML = ""; // Vider le tableau avant de le remplir

    presences.forEach(presence => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${presence.date}</td>
            <td>${presence.id}</td>
            <td>${presence.nom}</td>
            <td>${presence.prenom}</td>
            <td>${presence.qualite}</td>
            <td>${presence.annee || ""}</td>
            <td>${presence.email}</td>
            <td>${presence.numero}</td>
            <td>${presence.matricule || ""}</td>
            <td>${presence.annees_etude || ""}</td>
            <td>${presence.heure_arrive || ""}</td>
            <td>${presence.heure_sortie || ""}</td>
        `;

        tableBody.appendChild(row);
    });
}

// Appel de la fonction de filtrage après peuplement
function filterTable() {
    const searchInput = document.getElementById("searchInput").value.toLowerCase();
    const filterQualite = document.getElementById("filterQualite").value;
    const filterAnneeEtude = document.getElementById("filterAnneeEtude").value;
    const filterDate = document.getElementById("filterDate").value;
    const tableRows = document.querySelectorAll("#studentsTable tr");

    tableRows.forEach(row => {
        const cells = row.querySelectorAll("td");
        const date = cells[0]?.textContent || "";
        const qualite = cells[4]?.textContent || "";
        const anneeEtude = cells[9]?.textContent || "";
        const rowData = Array.from(cells).map(cell => cell.textContent.toLowerCase());

        const matchesSearch = rowData.some(data => data.includes(searchInput));
        const matchesQualite = !filterQualite || qualite === filterQualite;
        const matchesAnneeEtude = !filterAnneeEtude || anneeEtude === filterAnneeEtude;
        const matchesDate = !filterDate || date === filterDate;

        if (matchesSearch && matchesQualite && matchesAnneeEtude && matchesDate) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    });
}
