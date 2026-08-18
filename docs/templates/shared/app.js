// Catálogo de perfumes inspirados (masculinos, femininos, árabes e edições especiais).
// Compartilhado por todos os templates de cor em docs/perfumar_templates/.
const WHATSAPP_NUMBER = '5519981449696';

const REGULAR_SIZES = { sizes: '28ml e 100ml', price: 'A partir de R$ 70,00' };
const NOBLESSE_SIZES = { sizes: '10ml e 50ml', price: 'A partir de R$ 40,00' };

const productData = [
  // Masculinos
  { id: 'brz-urban', name: 'BRZ Urban', gender: 'masculino', note: 'Amadeirado Aromático', inspiration: '212 Vip Men (Carolina Herrera)', badge: 'Mais vendido', ...REGULAR_SIZES },
  { id: 'bravus', name: 'Bravus', gender: 'masculino', note: 'Amadeirado Especiado', inspiration: 'Bad Boy (Carolina Herrera)', ...REGULAR_SIZES },
  { id: 'charmy', name: 'Charmy', gender: 'masculino', note: 'Amadeirado Especiado', inspiration: '1 Million (Paco Rabanne)', ...REGULAR_SIZES },
  { id: 'brz-intense-men', name: 'BRZ Intense Men', gender: 'masculino', note: 'Amadeirado Picante', inspiration: '212 Sexy Men (Carolina Herrera)', ...REGULAR_SIZES },
  { id: 'conquest', name: 'Conquest', gender: 'masculino', note: 'Amadeirado Âmbar', inspiration: 'Invictus Victory (Paco Rabanne)', ...REGULAR_SIZES },
  { id: 'champion', name: 'Champion', gender: 'masculino', note: 'Aquático Amadeirado', inspiration: 'Invictus (Paco Rabanne)', ...REGULAR_SIZES },
  { id: 'brz-men', name: 'BRZ Men', gender: 'masculino', note: 'Cítrico Aromático', inspiration: '212 Men (Carolina Herrera)', ...REGULAR_SIZES },
  { id: 'elegante-sport', name: 'Elegante Sport', gender: 'masculino', note: 'Cítrico Fresco', inspiration: 'Allure Sport (Chanel)', ...REGULAR_SIZES },
  { id: 'personalz', name: 'Personalz', gender: 'masculino', note: 'Aromático Fougère', inspiration: 'Y (Yves Saint Laurent)', ...REGULAR_SIZES },
  { id: 'noble', name: 'Noble', gender: 'masculino', note: 'Amadeirado Aromático', inspiration: 'Gentleman (Givenchy)', ...REGULAR_SIZES },
  { id: 'blue', name: 'Blue', gender: 'masculino', note: 'Amadeirado Aromático', inspiration: 'Bleu de Chanel', ...REGULAR_SIZES },
  { id: 'selvagem', name: 'Selvagem', gender: 'masculino', note: 'Amadeirado Fresco', inspiration: 'Sauvage (Dior)', badge: 'Mais vendido', ...REGULAR_SIZES },
  { id: 'sweet-class', name: 'Sweet Class', gender: 'masculino', note: 'Amadeirado Clássico', inspiration: 'Pour Homme (Dolce & Gabbana)', ...REGULAR_SIZES },
  { id: 'silver-z', name: 'Silver Z', gender: 'masculino', note: 'Aromático Fresco', inspiration: 'Silver Scent (Jacques Bogart)', ...REGULAR_SIZES },
  { id: 'code-man', name: 'Code Man', gender: 'masculino', note: 'Oriental Amadeirado', inspiration: 'Armani Code (Giorgio Armani)', ...REGULAR_SIZES },
  { id: 'ahazzo', name: 'Ahazzo', gender: 'masculino', note: 'Aromático Fougère', inspiration: 'Azzaro Pour Homme', ...REGULAR_SIZES },
  { id: 'boss-man', name: 'Boss Man', gender: 'masculino', note: 'Amadeirado Especiado', inspiration: 'Boss Bottled (Hugo Boss)', ...REGULAR_SIZES },
  { id: 'mb-endless', name: 'MB. Endless', gender: 'masculino', note: 'Aromático Fresco', inspiration: 'Legend Spirit (Montblanc)', ...REGULAR_SIZES },
  { id: 'jump', name: 'Jump!', gender: 'masculino', note: 'Esportivo Aquático', inspiration: 'Fragrância esportiva internacional', ...REGULAR_SIZES },
  { id: 'lord', name: 'Lord', gender: 'masculino', note: 'Amadeirado Intenso', inspiration: 'Polo Black (Ralph Lauren)', ...REGULAR_SIZES },
  { id: 'strong', name: 'Strong', gender: 'masculino', note: 'Amadeirado Fumado', inspiration: 'Black (Bvlgari)', ...REGULAR_SIZES },
  { id: 'black-horse', name: 'Black Horse', gender: 'masculino', note: 'Amadeirado Especiado', inspiration: 'Black (Ferrari)', ...REGULAR_SIZES },
  { id: 'lord-green', name: 'Lord Green', gender: 'masculino', note: 'Aromático Verde', inspiration: 'Polo Green (Ralph Lauren)', ...REGULAR_SIZES },
  { id: 'animalz', name: 'Animalz', gender: 'masculino', note: 'Amadeirado Selvagem', inspiration: 'Animale for Men', ...REGULAR_SIZES },
  { id: 'loyal', name: 'Loyal', gender: 'masculino', note: 'Amadeirado Intenso', inspiration: 'Malbec (Bericato)', ...REGULAR_SIZES },
  { id: 'brz-dark', name: 'BRZ Dark', gender: 'masculino', note: 'Amadeirado Noturno', inspiration: '212 Vip Black (Carolina Herrera)', ...REGULAR_SIZES },
  { id: 'tauren', name: 'Tauren', gender: 'masculino', note: 'Aromático Fougère', inspiration: 'Fragrância aromática marcante', ...REGULAR_SIZES },
  { id: 'valien', name: 'Valien', gender: 'masculino', note: 'Amadeirado Futurista', inspiration: 'Phantom (Paco Rabanne)', badge: 'Novidade', ...REGULAR_SIZES },

  // Femininos
  { id: 'brz-blossom', name: 'BRZ Blossom', gender: 'feminino', note: 'Floral Frutado', inspiration: '212 Vip Rosé (Carolina Herrera)', ...REGULAR_SIZES },
  { id: 'brz-intense-woman', name: 'BRZ Intense Woman', gender: 'feminino', note: 'Floral Sensual', inspiration: '212 Sexy Feminino (Carolina Herrera)', ...REGULAR_SIZES },
  { id: 'luminous-flowers', name: 'Luminous Flowers', gender: 'feminino', note: 'Floral Adocicado', inspiration: 'Good Girl Blush (Carolina Herrera)', ...REGULAR_SIZES },
  { id: 'creta', name: 'Creta', gender: 'feminino', note: 'Floral Âmbar', inspiration: 'Olympéa Legend (Paco Rabanne)', ...REGULAR_SIZES },
  { id: 'luminous-girl', name: 'Luminous Girl', gender: 'feminino', note: 'Floral Oriental', inspiration: 'Good Girl (Carolina Herrera)', ...REGULAR_SIZES },
  { id: 'gold-woman', name: 'Gold Woman', gender: 'feminino', note: 'Floral Frutado', inspiration: 'Lady Million (Paco Rabanne)', badge: 'Mais vendido', ...REGULAR_SIZES },
  { id: 'brz-woman', name: 'BRZ Woman', gender: 'feminino', note: 'Floral Fresco', inspiration: '212 NYC Woman (Carolina Herrera)', ...REGULAR_SIZES },
  { id: 'lys', name: 'Lys', gender: 'feminino', note: 'Floral Delicado', inspiration: 'Lily (O Boticário)', ...REGULAR_SIZES },
  { id: 'miss', name: 'Miss', gender: 'feminino', note: 'Floral Chipre', inspiration: 'Coco Mademoiselle (Chanel)', badge: 'Mais vendido', ...REGULAR_SIZES },
  { id: 'love-it', name: 'Love It', gender: 'feminino', note: 'Floral Frutado', inspiration: "J'adore (Dior)", ...REGULAR_SIZES },
  { id: 'la-vie-est-amour', name: 'La Vie Est Amour', gender: 'feminino', note: 'Floral Gourmand', inspiration: 'La Vie Est Belle (Lancôme)', ...REGULAR_SIZES },
  { id: '2-love', name: '2 Love', gender: 'feminino', note: 'Floral Frutado', inspiration: 'Amor Amor (Cacharel)', ...REGULAR_SIZES },
  { id: 'beauty', name: 'Beauty', gender: 'feminino', note: 'Floral Suave', inspiration: 'Fragrância floral suave', ...REGULAR_SIZES },
  { id: 'tuberose-shine', name: 'Tuberose Shine', gender: 'feminino', note: 'Floral Branco', inspiration: 'My Way (Giorgio Armani)', ...REGULAR_SIZES },
  { id: 'autentica', name: 'Autêntica', gender: 'feminino', note: 'Floral Elegante', inspiration: "L'Interdit (Givenchy)", ...REGULAR_SIZES },
  { id: 'glow', name: 'Glow', gender: 'feminino', note: 'Floral Almiscarado', inspiration: 'Idôle (Lancôme)', ...REGULAR_SIZES },
  { id: 'cintilante', name: 'Cintilante', gender: 'feminino', note: 'Doce Gourmand', inspiration: 'Candy Gloss (Prada)', ...REGULAR_SIZES },
  { id: 'magic', name: 'Magic', gender: 'feminino', note: 'Doce Frutado', inspiration: 'Fantasy (Britney Spears)', ...REGULAR_SIZES },
  { id: 'gs', name: 'GS', gender: 'feminino', note: 'Floral Clássico', inspiration: 'Gabriela Sabatini', ...REGULAR_SIZES },
  { id: 'revolution', name: 'Revolution', gender: 'feminino', note: 'Floral Mel', inspiration: 'Scandal (Jean Paul Gaultier)', ...REGULAR_SIZES },
  { id: 'tresor', name: 'Trésor', gender: 'feminino', note: 'Oriental Floral', inspiration: 'Trésor La Nuit (Lancôme)', ...REGULAR_SIZES },
  { id: 'sweet-blue', name: 'Sweet Blue', gender: 'feminino', note: 'Cítrico Floral', inspiration: 'Light Blue (Dolce & Gabbana)', ...REGULAR_SIZES },
  { id: 'sweet', name: 'Sweet', gender: 'feminino', note: 'Doce Floral', inspiration: 'Fragrância doce envolvente', ...REGULAR_SIZES },
  { id: 'unique', name: 'Unique', gender: 'feminino', note: 'Floral Clássico', inspiration: 'Classique (Jean Paul Gaultier)', ...REGULAR_SIZES },
  { id: 'five-z', name: 'Five Z', gender: 'feminino', note: 'Floral Aldeídico', inspiration: 'Chanel Nº5', ...REGULAR_SIZES },
  { id: 'honey', name: 'Honey', gender: 'feminino', note: 'Doce Gourmand', inspiration: 'Angel (Mugler)', ...REGULAR_SIZES },
  { id: 'aura-rose', name: 'Aura Rose', gender: 'feminino', note: 'Floral Rosado', inspiration: 'Fragrância floral rosada', ...REGULAR_SIZES },
  { id: 'isis', name: 'Isis', gender: 'feminino', note: 'Floral Âmbar', inspiration: 'Olympéa (Paco Rabanne)', badge: 'Novidade', ...REGULAR_SIZES },

  // Árabes
  { id: 'golden-arabian', name: 'Golden Arabian', gender: 'arabe', note: 'Âmbar Dourado', inspiration: 'Kajal (Lamar)', ...REGULAR_SIZES },
  { id: 'rubi', name: 'Rubi', gender: 'arabe', note: 'Oriental Frutado', inspiration: 'Fragrância oriental frutada', ...REGULAR_SIZES },
  { id: 'dunes', name: 'Dunes', gender: 'arabe', note: 'Almíscar do Deserto', inspiration: 'Musk (The Spirit of Dubai)', badge: 'Mais vendido', ...REGULAR_SIZES },
  { id: 'sunshine', name: 'Sunshine', gender: 'arabe', note: 'Floral Almiscarado', inspiration: 'Sparkling (Kayali)', ...REGULAR_SIZES },
  { id: 'malirah', name: 'Malirah', gender: 'arabe', note: 'Frutado Almiscarado', inspiration: 'Yara (Lattafa)', ...REGULAR_SIZES },
  { id: 'najad', name: 'Najad', gender: 'arabe', note: 'Amadeirado Almiscarado', inspiration: 'Fakhar (Rasasi)', ...REGULAR_SIZES },
  { id: 'sharif', name: 'Sharif', gender: 'arabe', note: 'Âmbar Real', inspiration: 'The Kingdom (Lattafa)', ...REGULAR_SIZES },
  { id: 'zayan', name: 'Zayan', gender: 'arabe', note: 'Oriental Amadeirado', inspiration: 'Asad (Lattafa)', badge: 'Novidade', ...REGULAR_SIZES },

  // Linha 4 Estações + Noblesse (edições especiais)
  { id: 'primavera', name: 'Primavera', gender: 'especial', note: 'Floral Fresco', inspiration: 'Linha 4 Estações', ...REGULAR_SIZES },
  { id: 'verao', name: 'Verão', gender: 'especial', note: 'Cítrico Aquático', inspiration: 'Linha 4 Estações', ...REGULAR_SIZES },
  { id: 'outono', name: 'Outono', gender: 'especial', note: 'Amadeirado Quente', inspiration: 'Linha 4 Estações', ...REGULAR_SIZES },
  { id: 'inverno', name: 'Inverno', gender: 'especial', note: 'Oriental Envolvente', inspiration: 'Linha 4 Estações', badge: 'Novidade', ...REGULAR_SIZES },
  { id: 'yria', name: 'Yria', gender: 'especial', note: 'Floral Almiscarado de Luxo', inspiration: 'Delina (Parfums de Marly) · Linha Noblesse', badge: 'Mais vendido', ...NOBLESSE_SIZES },
  { id: 'darion', name: 'Darion', gender: 'especial', note: 'Amadeirado Frutado de Luxo', inspiration: 'Aventus (Creed) · Linha Noblesse', ...NOBLESSE_SIZES },
];

const genderLabels = { masculino: 'MASCULINO', feminino: 'FEMININO', arabe: 'ÁRABE', especial: 'EDIÇÃO ESPECIAL' };

// Fotos ficam em docs/perfumar_templates/shared/assets/products/<id>.jpg (compartilhadas por todos os templates).
const PHOTO_BASE_PATH = '../shared/assets/products/';

function buildWhatsappLink(product) {
  const message = `Olá! Vim pelo site e tenho interesse no perfume ${product.name} (inspirado em ${product.inspiration}). Pode me passar mais informações e valores?`;
  return `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(message)}`;
}

function normalize(text) {
  return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

function productCardHtml(product) {
  const badge = product.badge ? `<span class="product-badge">${product.badge}</span>` : '';
  return `
    <article class="product-card" data-category="${product.gender}" data-search="${normalize(product.name + ' ' + product.inspiration + ' ' + product.note)}">
      <div class="product-media g-${product.gender}">
        ${badge}
        <button class="favorite" aria-label="Favoritar ${product.name}">♡</button>
        <img class="product-photo" data-id="${product.id}" data-step="jpg" src="${PHOTO_BASE_PATH}${product.id}.jpg" alt="${product.name}" loading="lazy">
        <div class="mini-bottle"></div>
      </div>
      <div class="product-info">
        <span class="product-category">${genderLabels[product.gender]} • ${product.note.toUpperCase()}</span>
        <h3>${product.name}</h3>
        <p class="product-inspiration">Inspirado em: ${product.inspiration}</p>
        <div class="price-line"><strong>${product.price}</strong><span>${product.sizes}</span></div>
        <a class="product-button" href="${buildWhatsappLink(product)}" target="_blank" rel="noopener">Comprar no WhatsApp <span>→</span></a>
      </div>
    </article>`;
}

const productGrid = document.getElementById('productGrid');
const catalogCount = document.getElementById('catalogCount');
productGrid.innerHTML = productData.map(productCardHtml).join('');

let currentGenderFilter = 'todos';
let currentSearchTerm = '';

function applyFilters() {
  const cards = productGrid.querySelectorAll('.product-card');
  let visibleCount = 0;
  cards.forEach((card) => {
    const matchesGender = currentGenderFilter === 'todos' || card.dataset.category === currentGenderFilter;
    const matchesSearch = !currentSearchTerm || card.dataset.search.includes(currentSearchTerm);
    const visible = matchesGender && matchesSearch;
    card.classList.toggle('hidden', !visible);
    if (visible) visibleCount += 1;
  });
  if (catalogCount) catalogCount.textContent = `Mostrando ${visibleCount} de ${productData.length} perfumes`;
  bindFavoriteButtons();
}

function bindFavoriteButtons() {
  productGrid.querySelectorAll('.favorite').forEach((button) => {
    if (button.dataset.bound) return;
    button.dataset.bound = 'true';
    button.addEventListener('click', () => {
      const active = button.classList.toggle('active');
      button.textContent = active ? '♥' : '♡';
      favorites += active ? 1 : -1;
      document.getElementById('favoriteCount').textContent = favorites;
    });
  });
}

// Falls back .jpg -> .png -> generated .svg illustration -> decorative icon.
function bindPhotoFallbacks() {
  productGrid.querySelectorAll('img.product-photo').forEach((img) => {
    if (img.dataset.bound) return;
    img.dataset.bound = 'true';
    img.addEventListener('error', () => {
      if (img.dataset.step === 'jpg') {
        img.dataset.step = 'png';
        img.src = `${PHOTO_BASE_PATH}${img.dataset.id}.png`;
      } else if (img.dataset.step === 'png') {
        img.dataset.step = 'svg';
        img.src = `${PHOTO_BASE_PATH}${img.dataset.id}.svg`;
      } else {
        img.style.display = 'none';
      }
    });
  });
}

let favorites = 0;
applyFilters();
bindPhotoFallbacks();

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
const categoryButtons = document.querySelectorAll('.category-card[data-filter]');
const navFilterLinks = document.querySelectorAll('.main-nav a[data-filter], .footer a[data-filter]');

function setGenderFilter(filter) {
  currentGenderFilter = filter;
  tabs.forEach((tab) => tab.classList.toggle('active', tab.dataset.filter === filter));
  applyFilters();
}

tabs.forEach((tab) => {
  tab.addEventListener('click', () => setGenderFilter(tab.dataset.filter));
});

categoryButtons.forEach((button) => {
  button.addEventListener('click', () => {
    setGenderFilter(button.dataset.filter);
    document.querySelector('#catalogo').scrollIntoView({ behavior: 'smooth' });
  });
});

navFilterLinks.forEach((link) => {
  link.addEventListener('click', () => setGenderFilter(link.dataset.filter));
});

const catalogSearch = document.getElementById('catalogSearch');
catalogSearch.addEventListener('input', () => {
  currentSearchTerm = normalize(catalogSearch.value.trim());
  applyFilters();
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

function runOverlaySearch(term) {
  catalogSearch.value = term;
  currentSearchTerm = normalize(term);
  applyFilters();
  closeSearch();
  document.querySelector('#catalogo').scrollIntoView({ behavior: 'smooth' });
}

searchInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') runOverlaySearch(searchInput.value);
});

document.querySelectorAll('.quick-search button').forEach((button) => {
  button.addEventListener('click', () => runOverlaySearch(button.textContent));
});

const menuToggle = document.querySelector('.menu-toggle');
const mainNav = document.querySelector('.main-nav');
menuToggle.addEventListener('click', () => {
  const open = mainNav.classList.toggle('open');
  menuToggle.setAttribute('aria-expanded', String(open));
});
mainNav.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => mainNav.classList.remove('open')));
