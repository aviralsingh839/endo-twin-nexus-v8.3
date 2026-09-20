// CHRONO-PCOS V8.3+ Website - Highly Polished Extensive Scientific Project Website - Professional, Modern, Credible, Human, Innovative
// Minimal JS, no excessive animations, no fake medical claims, smooth scrolling, interactive diagrams

document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for nav links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                // Update URL without jump
                history.pushState(null, null, this.getAttribute('href'));
            }
        });
    });

    // Highlight active nav link on scroll
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');

    function highlightNav() {
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (window.scrollY >= (sectionTop - 100)) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.style.background = '';
            link.style.color = '';
            if (link.getAttribute('href') === '#' + current) {
                link.style.background = 'rgba(14,165,233,0.2)';
                link.style.color = 'white';
            }
        });
    }

    window.addEventListener('scroll', highlightNav);
    highlightNav();

    // Add subtle fade-in for cards on scroll (no excessive animations)
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    document.querySelectorAll('.card, .tech-card, .app-card, .flow-step, .timeline-item').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(10px)';
        el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        observer.observe(el);
    });

    // Log scientific integrity
    console.log('CHRONO-PCOS V8.3+ - Research prototype, not a medical device');
    console.log('Sense • Model • Predict • Personalize • Connect');
    console.log('Local-first, offline, privacy-focused, honest limitations');
    console.log('MEASURED, CLINICALLY ENTERED, IMAGE-DERIVED, MODEL-INFERRED, UNKNOWN - Never fabricate');
    console.log('No fake medical claims, no fake statistics, no fake testimonials, no stock-photo overload');
    console.log('Scientific, technical, modern, credible, human, innovative');
    console.log('Garuda Linux Ready: Dolphin → LAUNCH → COMPLETE_LAUNCHER.sh → Control Center');
    console.log('Website: Professional public-facing CHRONO-PCOS research/innovation platform');
});
