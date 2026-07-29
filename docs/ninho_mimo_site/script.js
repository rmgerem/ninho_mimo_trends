const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll('.reveal').forEach((element) => revealObserver.observe(element));

const tabs = document.querySelectorAll('.tab');
const categoryButtons = document.querySelectorAll('.category-card');
const productCards = document.querySelectorAll('.product-card');

function filterProducts(filter) {
  productCards.forEach((card) => {
    const categories = card.dataset.category.split(' ');
    card.classList.toggle('hidden', filter !== 'todos' && !categories.includes(filter));
  });
  document.querySelector('#destaques').scrollIntoView({ behavior: 'smooth' });
}

tabs.forEach((tab) => {
  tab.addEventListener('click', () => {
    tabs.forEach((item) => item.classList.remove('active'));
    tab.classList.add('active');
    filterProducts(tab.dataset.filter);
  });
});

categoryButtons.forEach((button) => {
  button.addEventListener('click', () => {
    const filter = button.dataset.filter;
    tabs.forEach((tab) => tab.classList.toggle('active', tab.dataset.filter === filter));
    filterProducts(filter);
  });
});

let favorites = 0;
document.querySelectorAll('.favorite').forEach((button) => {
  button.addEventListener('click', () => {
    const active = button.classList.toggle('active');
    button.textContent = active ? '♥' : '♡';
    favorites += active ? 1 : -1;
    document.getElementById('favoriteCount').textContent = favorites;
  });
});

const searchOverlay = document.getElementById('searchOverlay');
const searchInput = document.getElementById('searchInput');
document.getElementById('searchButton').addEventListener('click', () => {
  searchOverlay.classList.add('open');
  searchOverlay.setAttribute('aria-hidden', 'false');
  setTimeout(() => searchInput.focus(), 150);
});
document.getElementById('closeSearch').addEventListener('click', closeSearch);
searchOverlay.addEventListener('click', (event) => {
  if (event.target === searchOverlay) closeSearch();
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') closeSearch();
});
function closeSearch() {
  searchOverlay.classList.remove('open');
  searchOverlay.setAttribute('aria-hidden', 'true');
}

document.querySelectorAll('.quick-search button').forEach((button) => {
  button.addEventListener('click', () => {
    searchInput.value = button.textContent;
    searchInput.focus();
  });
});

const newsletterForm = document.getElementById('newsletterForm');
newsletterForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const email = document.getElementById('email').value;
  document.getElementById('formMessage').textContent = `Pronto! ${email} entrou para o nosso ninho ♡`;
  newsletterForm.reset();
});

const menuToggle = document.querySelector('.menu-toggle');
const mainNav = document.querySelector('.main-nav');
menuToggle.addEventListener('click', () => {
  const open = mainNav.classList.toggle('open');
  menuToggle.setAttribute('aria-expanded', String(open));
});
mainNav.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => mainNav.classList.remove('open')));

document.getElementById('loadMore').addEventListener('click', (event) => {
  event.currentTarget.textContent = 'Novos achadinhos em breve ♡';
  event.currentTarget.disabled = true;
});
