// JavaScript principal pour l'application Club de Plongée

document.addEventListener('DOMContentLoaded', function() {
    
    // Initialisation des tooltips Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialisation des popovers Bootstrap
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Gestion des formulaires avec validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Filtrage dynamique des compétences selon la section
    const sectionSelect = document.getElementById('id_section');
    const competencesSelect = document.getElementById('id_competences');
    
    if (sectionSelect && competencesSelect) {
        sectionSelect.addEventListener('change', function() {
            const sectionId = this.value;
            if (sectionId) {
                fetch(`/api/competences-section/?section_id=${sectionId}`)
                    .then(response => response.json())
                    .then(data => {
                        competencesSelect.innerHTML = '<option value="">---------</option>';
                        data.competences.forEach(competence => {
                            const option = document.createElement('option');
                            option.value = competence.id;
                            option.textContent = competence.nom;
                            competencesSelect.appendChild(option);
                        });
                    })
                    .catch(error => {
                        console.error('Erreur lors du chargement des compétences:', error);
                    });
            } else {
                competencesSelect.innerHTML = '<option value="">---------</option>';
            }
        });
    }

    // Amélioration des évaluations par étoiles
    const starRatings = document.querySelectorAll('.star-rating');
    starRatings.forEach(rating => {
        const stars = rating.querySelectorAll('input[type="radio"]');
        const labels = rating.querySelectorAll('label');
        
        stars.forEach((star, index) => {
            star.addEventListener('change', function() {
                // Mettre à jour l'affichage des étoiles
                labels.forEach((label, labelIndex) => {
                    if (labelIndex < stars.length - 1 - this.value) {
                        label.style.color = '#ffc107';
                    } else {
                        label.style.color = '#ddd';
                    }
                });
            });
        });
    });

    // Confirmation de suppression
    const deleteButtons = document.querySelectorAll('.btn-danger');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Êtes-vous sûr de vouloir supprimer cet élément ? Cette action est irréversible.')) {
                e.preventDefault();
            }
        });
    });

    // Gestion personnalisée des messages
    const messageAlerts = document.querySelectorAll('.message-alert');
    messageAlerts.forEach(alert => {
        const messageType = alert.getAttribute('data-message-type');
        
        // Les messages de succès et d'erreur ne disparaissent pas automatiquement
        if (messageType === 'success' || messageType === 'error') {
            // Pas d'auto-hide pour ces types de messages
            return;
        }
        
        // Les messages d'info disparaissent après 5 secondes
        if (messageType === 'info') {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
        
        // Les messages d'avertissement disparaissent après 8 secondes
        if (messageType === 'warning') {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 8000);
        }
    });

    // Amélioration de la recherche
    const searchInput = document.querySelector('input[name="q"]');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.form.submit();
            }, 500);
        });
    }

    // Lazy loading des images
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));

    // Amélioration de l'expérience mobile
    if (window.innerWidth <= 768) {
        // Réduire la taille des boutons sur mobile
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(button => {
            button.classList.add('btn-sm');
        });

        // Améliorer la navigation sur mobile
        const dropdowns = document.querySelectorAll('.dropdown-toggle');
        dropdowns.forEach(dropdown => {
            dropdown.addEventListener('click', function(e) {
                e.preventDefault();
                const menu = this.nextElementSibling;
                menu.classList.toggle('show');
            });
        });
    }

    // Gestion des formulaires de séance
    const seanceForm = document.querySelector('form[action*="seance"]');
    if (seanceForm) {
        const elevesSelect = document.getElementById('id_eleves');
        const competencesSelect = document.getElementById('id_competences');
        
        if (elevesSelect && competencesSelect) {
            // Validation : au moins un élève et une compétence
            seanceForm.addEventListener('submit', function(e) {
                if (elevesSelect.selectedOptions.length === 0) {
                    e.preventDefault();
                    alert('Veuillez sélectionner au moins un élève.');
                    return;
                }
                
                if (competencesSelect.selectedOptions.length === 0) {
                    e.preventDefault();
                    alert('Veuillez sélectionner au moins une compétence.');
                    return;
                }
            });
        }
    }

    // Amélioration de l'accessibilité
    const focusableElements = document.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    
    // Gestion de la navigation au clavier
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            document.body.classList.add('keyboard-navigation');
        }
    });

    document.addEventListener('mousedown', function() {
        document.body.classList.remove('keyboard-navigation');
    });

    // Amélioration des tableaux
    const tables = document.querySelectorAll('.table');
    tables.forEach(table => {
        // Ajouter des classes pour le style
        table.classList.add('table-hover');
        
        // Améliorer l'accessibilité
        const headers = table.querySelectorAll('th');
        headers.forEach(header => {
            header.setAttribute('scope', 'col');
        });
    });

    // Gestion des liens externes
    const externalLinks = document.querySelectorAll('a[href^="http"]');
    externalLinks.forEach(link => {
        link.setAttribute('target', '_blank');
        link.setAttribute('rel', 'noopener noreferrer');
    });

    // Amélioration de l'expérience utilisateur
    const loadingStates = document.querySelectorAll('[data-loading]');
    loadingStates.forEach(element => {
        element.addEventListener('click', function() {
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Chargement...';
            this.disabled = true;
            
            // Restaurer après un délai (pour les actions qui ne rechargent pas la page)
            setTimeout(() => {
                this.innerHTML = originalText;
                this.disabled = false;
            }, 2000);
        });
    });

    // Gestion des messages de succès/erreur
    const messages = document.querySelectorAll('.alert');
    messages.forEach(message => {
        // Ajouter un bouton de fermeture si pas déjà présent
        if (!message.querySelector('.btn-close')) {
            const closeButton = document.createElement('button');
            closeButton.type = 'button';
            closeButton.className = 'btn-close';
            closeButton.setAttribute('data-bs-dismiss', 'alert');
            closeButton.setAttribute('aria-label', 'Fermer');
            message.appendChild(closeButton);
        }
    });

    // Amélioration de la pagination
    const pagination = document.querySelector('.pagination');
    if (pagination) {
        const pageLinks = pagination.querySelectorAll('.page-link');
        pageLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                // Ajouter un indicateur de chargement
                const loadingIndicator = document.createElement('div');
                loadingIndicator.className = 'position-fixed top-50 start-50 translate-middle';
                loadingIndicator.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Chargement...</span></div>';
                document.body.appendChild(loadingIndicator);
            });
        });
    }

    // Gestion des formulaires d'évaluation
    const evaluationForms = document.querySelectorAll('form[action*="evaluation"]');
    evaluationForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('input[required]');
            let allFilled = true;
            
            requiredFields.forEach(field => {
                if (!field.checked && field.type === 'radio') {
                    allFilled = false;
                }
            });
            
            if (!allFilled) {
                e.preventDefault();
                alert('Veuillez évaluer toutes les compétences requises.');
            }
        });
    });

    console.log('Application Club de Plongée initialisée avec succès !');
}); 