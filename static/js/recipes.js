/**
 * recipes.js - JavaScript для работы с рецептурным журналом
 */

// Конфигурация
const RECIPES_CONFIG = {
    localStorageKeys: {
        recipes: 'vetgid_recipes',
        drugs: 'vetgid_drugs',
        blanks: 'vetgid_blanks',
        consents: 'vetgid_consents',
        lastRecipeNumber: 'vetgid_last_recipe_number'
    },
    itemsPerPage: 10
};

// Глобальные переменные
let currentRecipesPage = 1;
let currentDrugsPage = 1;
let currentBlanksPage = 1;
let allRecipes = [];
let allDrugs = [];
let allBlanks = [];
let allConsents = [];
let serverDrugs = []; // Препараты с сервера для реестра

// Инициализация данных
function initData() {
    // Загрузка данных из localStorage
    const recipesData = localStorage.getItem(RECIPES_CONFIG.localStorageKeys.recipes);
    const drugsData = localStorage.getItem(RECIPES_CONFIG.localStorageKeys.drugs);
    const blanksData = localStorage.getItem(RECIPES_CONFIG.localStorageKeys.blanks);
    const consentsData = localStorage.getItem(RECIPES_CONFIG.localStorageKeys.consents);
    
    allRecipes = recipesData ? JSON.parse(recipesData) : [];
    allDrugs = drugsData ? JSON.parse(drugsData) : getDefaultDrugs();
    allBlanks = blanksData ? JSON.parse(blanksData) : [];
    allConsents = consentsData ? JSON.parse(consentsData) : [];
    
    // Сохранение обновленных данных (если были добавлены препараты по умолчанию)
    if (!drugsData) {
        saveDrugs();
    }
}

// Получение препаратов по умолчанию
function getDefaultDrugs() {
    return [
        {
            id: 1,
            name: "Амоксициллин 250 мг",
            activeSubstance: "Амоксициллин",
            registrationNumber: "ЛП-001234",
            form: "tablets",
            prescriptionRequired: true
        },
        {
            id: 2,
            name: "Цефтриаксон 1 г",
            activeSubstance: "Цефтриаксон",
            registrationNumber: "ЛП-002345",
            form: "injections",
            prescriptionRequired: true
        },
        {
            id: 3,
            name: "Энтеросгель",
            activeSubstance: "Полиметилсилоксана полигидрат",
            registrationNumber: "ЛП-003456",
            form: "suspension",
            prescriptionRequired: false
        },
        {
            id: 4,
            name: "Фуросемид 40 мг",
            activeSubstance: "Фуросемид",
            registrationNumber: "ЛП-004567",
            form: "tablets",
            prescriptionRequired: true
        },
        {
            id: 5,
            name: "Гамавит",
            activeSubstance: "Экстракт плаценты",
            registrationNumber: "ЛП-005678",
            form: "injections",
            prescriptionRequired: false
        }
    ];
}

// Сохранение данных
function saveRecipes() {
    localStorage.setItem(RECIPES_CONFIG.localStorageKeys.recipes, JSON.stringify(allRecipes));
}

function saveDrugs() {
    localStorage.setItem(RECIPES_CONFIG.localStorageKeys.drugs, JSON.stringify(allDrugs));
}

function saveBlanks() {
    localStorage.setItem(RECIPES_CONFIG.localStorageKeys.blanks, JSON.stringify(allBlanks));
}

function saveConsents() {
    localStorage.setItem(RECIPES_CONFIG.localStorageKeys.consents, JSON.stringify(allConsents));
}

// Генерация ID
function generateId(items) {
    return items.length > 0 ? Math.max(...items.map(item => item.id)) + 1 : 1;
}

// Генерация номера рецепта
function generateRecipeNumber() {
    const lastNumber = localStorage.getItem(RECIPES_CONFIG.localStorageKeys.lastRecipeNumber);
    let nextNumber = lastNumber ? parseInt(lastNumber) + 1 : 1;
    
    // Форматирование с ведущими нулями
    const formattedNumber = nextNumber.toString().padStart(6, '0');
    document.getElementById('recipeNumber').value = formattedNumber;
    
    // Сохранение последнего номера
    localStorage.setItem(RECIPES_CONFIG.localStorageKeys.lastRecipeNumber, nextNumber.toString());
    
    return formattedNumber;
}

// Загрузка рецептов
function loadRecipes(page = 1) {
    currentRecipesPage = page;
    
    const searchTerm = document.getElementById('searchRecipes').value.toLowerCase();
    const filterDate = document.getElementById('filterDate').value;
    const filterStatus = document.getElementById('filterStatus').value;
    
    // Фильтрация рецептов
    let filteredRecipes = allRecipes.filter(recipe => {
        // Поиск по всем текстовым полям
        if (searchTerm) {
            const searchFields = [
                recipe.number,
                recipe.ownerName,
                recipe.animalType,
                recipe.animalName,
                recipe.drugName,
                recipe.activeSubstance,
                recipe.doctorName
            ].join(' ').toLowerCase();
            
            if (!searchFields.includes(searchTerm)) {
                return false;
            }
        }
        
        // Фильтр по дате
        if (filterDate && recipe.issueDate !== filterDate) {
            return false;
        }
        
        // Фильтр по статусу
        if (filterStatus && recipe.status !== filterStatus) {
            return false;
        }
        
        return true;
    });
    
    // Сортировка по дате (новые сначала)
    filteredRecipes.sort((a, b) => new Date(b.issueDate) - new Date(a.issueDate));
    
    // Пагинация
    const totalPages = Math.ceil(filteredRecipes.length / RECIPES_CONFIG.itemsPerPage);
    const startIndex = (page - 1) * RECIPES_CONFIG.itemsPerPage;
    const endIndex = startIndex + RECIPES_CONFIG.itemsPerPage;
    const pageRecipes = filteredRecipes.slice(startIndex, endIndex);
    
    // Отображение таблицы
    const tbody = document.getElementById('recipesTableBody');
    tbody.innerHTML = '';
    
    if (pageRecipes.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center py-4">
                    <div class="text-muted">
                        <i class="fas fa-inbox fa-2x mb-2"></i>
                        <p>Рецепты не найдены</p>
                    </div>
                </td>
            </tr>
        `;
    } else {
        pageRecipes.forEach(recipe => {
            const row = document.createElement('tr');
            
            // Определение статуса
            let statusText = '';
            let statusClass = '';
            switch (recipe.status) {
                case 'prescribed':
                    statusText = 'Выписан';
                    statusClass = 'status-prescribed';
                    break;
                case 'dispensed':
                    statusText = 'Отпущен';
                    statusClass = 'status-dispensed';
                    break;
                case 'expired':
                    statusText = 'Просрочен';
                    statusClass = 'status-expired';
                    break;
                default:
                    statusText = 'Неизвестно';
                    statusClass = '';
            }
            
            // Определение типа животного
            const animalTypeNames = {
                'cat': 'Кошка',
                'dog': 'Собака',
                'horse': 'Лошадь',
                'cattle': 'КРС',
                'rodent': 'Грызуны',
                'rabbit': 'Кролики',
                'bird': 'Птицы',
                'other': 'Другое'
            };
            
            const animalType = animalTypeNames[recipe.animalType] || recipe.animalType;
            const animalText = recipe.animalName ? `${animalType}, ${recipe.animalName}` : animalType;
            
            row.innerHTML = `
                <td>${recipe.number}</td>
                <td>${formatDate(recipe.issueDate)}</td>
                <td>${recipe.ownerName}</td>
                <td>${animalText}</td>
                <td>${recipe.drugName}</td>
                <td>${recipe.activeSubstance || '—'}</td>
                <td>${recipe.doctorName}</td>
                <td><span class="badge bg-info">${recipe.groupId || '—'}</span></td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="editRecipe(${recipe.id})" title="Редактировать">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-outline-success" onclick="printRecipe(${recipe.id})" title="Печать">
                            <i class="fas fa-print"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="deleteRecipe(${recipe.id})" title="Удалить">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            
            tbody.appendChild(row);
        });
    }
    
    // Обновление счетчика
    document.getElementById('recipesCount').textContent = 
        `Показано ${pageRecipes.length} из ${filteredRecipes.length} рецептов`;
    
    // Обновление пагинации
    updatePagination('recipesPagination', page, totalPages, loadRecipes);
}

// Загрузка препаратов (справочник) с поиском и пагинацией
function loadDrugs(page = 1) {
    const searchTerm = document.getElementById('searchDrugs') ? document.getElementById('searchDrugs').value.toLowerCase() : '';
    const tbody = document.getElementById('drugsTableBody');
    tbody.innerHTML = '';
    
    // Фильтрация препаратов по поисковому запросу
    let filteredDrugs = allDrugs;
    if (searchTerm) {
        filteredDrugs = allDrugs.filter(drug => {
            const searchFields = [
                drug.name || '',
                drug.activeSubstance || '',
                drug.registrationNumber || '',
                drug.manufacturer || '',
                drug.form || ''
            ].join(' ').toLowerCase();
            
            return searchFields.includes(searchTerm);
        });
    }
    
    if (filteredDrugs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-4">
                    <div class="text-muted">
                        <i class="fas fa-pills fa-2x mb-2"></i>
                        <p>Препараты не найдены</p>
                        ${searchTerm ? '<p>Попробуйте изменить поисковый запрос</p>' : ''}
                        <button class="btn btn-primary btn-sm" data-bs-toggle="modal" data-bs-target="#addDrugModal">
                            Добавить первый препарат
                        </button>
                    </div>
                </td>
            </tr>
        `;
    } else {
        // Пагинация
        const totalPages = Math.ceil(filteredDrugs.length / RECIPES_CONFIG.itemsPerPage);
        const startIndex = (page - 1) * RECIPES_CONFIG.itemsPerPage;
        const endIndex = startIndex + RECIPES_CONFIG.itemsPerPage;
        const pageDrugs = filteredDrugs.slice(startIndex, endIndex);
        
        pageDrugs.forEach(drug => {
            const row = document.createElement('tr');
            
            // Определение формы выпуска
            const formNames = {
                'tablets': 'Таблетки',
                'injections': 'Инъекции',
                'drops': 'Капли',
                'ointment': 'Мазь',
                'suspension': 'Суспензия',
                'capsules': 'Капсулы',
                'powder': 'Порошок',
                'solution': 'Раствор',
                'other': 'Другое'
            };
            
            const formText = formNames[drug.form] || drug.form;
            
            // Формирование концентрации
            let concentrationText = '';
            if (drug.concentration) {
                concentrationText = drug.concentration;
                if (drug.unit) {
                    concentrationText += ` ${drug.unit}`;
                }
            }
            
            row.innerHTML = `
                <td>${drug.name}</td>
                <td>${drug.activeSubstance}</td>
                <td>${concentrationText || '—'}</td>
                <td>${drug.registrationNumber || '—'}</td>
                <td>${formText}</td>
                <td>${drug.manufacturer || '—'}</td>
                <td>
                    <span class="badge ${drug.prescriptionRequired ? 'bg-danger' : 'bg-success'}">
                        ${drug.prescriptionRequired ? 'Рецептурный' : 'Без рецепта'}
                    </span>
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="editDrug(${drug.id})" title="Редактировать">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="deleteDrug(${drug.id})" title="Удалить">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            
            tbody.appendChild(row);
        });
        
        // Обновление счетчика
        if (document.getElementById('drugsCount')) {
            document.getElementById('drugsCount').textContent = 
                `Показано ${pageDrugs.length} из ${filteredDrugs.length} препаратов`;
        }
        
        // Обновление пагинации
        if (document.getElementById('drugsPagination')) {
            updatePagination('drugsPagination', page, totalPages, loadDrugs);
        }
    }
}

// Загрузка бланков
function loadBlanks() {
    const tbody = document.getElementById('blanksTableBody');
    tbody.innerHTML = '';
    
    if (allBlanks.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4">
                    <div class="text-muted">
                        <i class="fas fa-file-contract fa-2x mb-2"></i>
                        <p>Бланки не найдены</p>
                        <button class="btn btn-primary btn-sm" data-bs-toggle="modal" data-bs-target="#addBlankModal">
                            Добавить первый бланк
                        </button>
                    </div>
                </td>
            </tr>
        `;
    } else {
        allBlanks.forEach(blank => {
            const row = document.createElement('tr');
            
            // Определение статуса
            let statusText = '';
            let statusClass = '';
            switch (blank.status) {
                case 'issued':
                    statusText = 'Выдан';
                    statusClass = 'bg-info';
                    break;
                case 'used':
                    statusText = 'Использован';
                    statusClass = 'bg-success';
                    break;
                case 'cancelled':
                    statusText = 'Аннулирован';
                    statusClass = 'bg-danger';
                    break;
                default:
                    statusText = 'Неизвестно';
                    statusClass = 'bg-secondary';
            }
            
            row.innerHTML = `
                <td>${blank.number}</td>
                <td>${formatDate(blank.issueDate)}</td>
                <td>${blank.doctor}</td>
                <td>${blank.recipeNumber || '—'}</td>
                <td><span class="badge ${statusClass}">${statusText}</span></td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="editBlank(${blank.id})" title="Редактировать">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="deleteBlank(${blank.id})" title="Удалить">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            
            tbody.appendChild(row);
        });
    }
}

// Загрузка реестра препаратов
function loadRegistry(page = 1) {
    const searchTerm = document.getElementById('searchRegistry').value.toLowerCase();
    const tbody = document.getElementById('registryTableBody');
    tbody.innerHTML = '';
    
    // Загрузка препаратов с сервера
    fetch('/api/drugs/list')
    .then(response => response.json())
    .then(data => {
        if (data.drugs && data.drugs.length > 0) {
            // Сохраняем препараты с сервера в глобальную переменную
            serverDrugs = data.drugs;
            
            // Фильтрация по поисковому запросу
            let filteredDrugs = data.drugs;
            if (searchTerm) {
                filteredDrugs = data.drugs.filter(drug => {
                    const searchFields = [
                        drug.name || '',
                        drug.activeSubstance || '',
                        drug.registrationNumber || '',
                        drug.manufacturer || '',
                        drug.form || '',
                        drug.indications || '',
                        drug.contraindications || '',
                        drug.sideEffects || ''
                    ].join(' ').toLowerCase();
                    
                    return searchFields.includes(searchTerm);
                });
            }
            
            // Пагинация
            const totalPages = Math.ceil(filteredDrugs.length / RECIPES_CONFIG.itemsPerPage);
            const startIndex = (page - 1) * RECIPES_CONFIG.itemsPerPage;
            const endIndex = startIndex + RECIPES_CONFIG.itemsPerPage;
            const pageDrugs = filteredDrugs.slice(startIndex, endIndex);
            
            if (pageDrugs.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="8" class="text-center py-4">
                            <div class="text-muted">
                                <i class="fas fa-search fa-2x mb-2"></i>
                                <p>Препараты не найдены</p>
                            </div>
                        </td>
                    </tr>
                `;
            } else {
                pageDrugs.forEach(drug => {
                    const row = document.createElement('tr');
                    
                    // Обрезка длинного текста показаний
                    let indicationsText = drug.indications || '';
                    if (indicationsText.length > 100) {
                        indicationsText = indicationsText.substring(0, 100) + '...';
                    }
                    
                    row.innerHTML = `
                        <td>${drug.name || '—'}</td>
                        <td>${drug.activeSubstance || '—'}</td>
                        <td>${drug.registrationNumber || '—'}</td>
                        <td>${drug.manufacturer || '—'}</td>
                        <td>${drug.form || '—'}</td>
                        <td>${indicationsText}</td>
                        <td>
                            <span class="badge ${drug.prescriptionRequired ? 'bg-danger' : 'bg-success'}">
                                ${drug.prescriptionRequired ? 'Рецептурный' : 'Без рецепта'}
                            </span>
                        </td>
                        <td>
                            <button class="btn btn-sm btn-outline-info" onclick="viewDrugDetailsFromRegistry(${drug.id})" title="Подробнее">
                                <i class="fas fa-eye"></i>
                            </button>
                        </td>
                    `;
                    
                    tbody.appendChild(row);
                });
            }
            
            // Обновление счетчика
            document.getElementById('registryCount').textContent = 
                `Показано ${pageDrugs.length} из ${filteredDrugs.length} препаратов`;
            
            // Обновление пагинации
            updatePagination('registryPagination', page, totalPages, loadRegistry);
        } else {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-4">
                        <div class="text-muted">
                            <i class="fas fa-database fa-2x mb-2"></i>
                            <p>Реестр препаратов пуст</p>
                            <button class="btn btn-primary btn-sm" data-bs-toggle="modal" data-bs-target="#importDrugsModal">
                                Импортировать препараты
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }
    })
    .catch(error => {
        console.error('Ошибка загрузки реестра препаратов:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-4">
                    <div class="text-danger">
                        <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                        <p>Ошибка загрузки данных</p>
                        <small>${error.message}</small>
                    </div>
                </td>
            </tr>
        `;
    });
}

// Просмотр деталей препарата
function viewDrugDetails(drugId) {
    // Поиск препарата в локальном списке по ID
    const drug = allDrugs.find(d => d.id === drugId);
    if (drug) {
        showDrugDetailsModal(drug);
    } else {
        showAlert('Препарат не найден', 'error');
    }
}

// Просмотр деталей препарата из реестра
function viewDrugDetailsFromRegistry(drugId) {
    // Поиск препарата в списке серверных препаратов по ID
    const drug = serverDrugs.find(d => d.id === drugId);
    if (drug) {
        showDrugDetailsModal(drug);
    } else {
        // Если не найден в серверных препаратах, ищем в локальных
        viewDrugDetails(drugId);
    }
}

// Показать модальное окно с деталями препарата
function showDrugDetailsModal(drug) {
    // Создание модального окна с деталями
    const modalHtml = `
        <div class="modal fade" id="drugDetailsModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${drug.name || 'Препарат'}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>Основная информация</h6>
                                <table class="table table-sm">
                                    <tr><th>Действующее вещество:</th><td>${drug.activeSubstance || '—'}</td></tr>
                                    <tr><th>Регистрационный №:</th><td>${drug.registrationNumber || '—'}</td></tr>
                                    <tr><th>Производитель:</th><td>${drug.manufacturer || '—'}</td></tr>
                                    <tr><th>Форма выпуска:</th><td>${drug.form || '—'}</td></tr>
                                    <tr><th>Концентрация:</th><td>${drug.concentration || '—'} ${drug.unit || ''}</td></tr>
                                    <tr><th>Срок годности:</th><td>${drug.shelfLife ? drug.shelfLife + ' месяцев' : '—'}</td></tr>
                                    <tr><th>Рецептурный:</th><td>${drug.prescriptionRequired ? 'Да' : 'Нет'}</td></tr>
                                </table>
                            </div>
                            <div class="col-md-6">
                                <h6>Дополнительная информация</h6>
                                <div class="mb-3">
                                    <strong>Описание:</strong>
                                    <p>${drug.description || '—'}</p>
                                </div>
                                <div class="mb-3">
                                    <strong>Способ применения:</strong>
                                    <p>${drug.usageInstructions || '—'}</p>
                                </div>
                                <div class="mb-3">
                                    <strong>Особые указания:</strong>
                                    <p>${drug.specialInstructions || '—'}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
                        <button type="button" class="btn btn-primary" onclick="useDrugInRecipe('${drug.name.replace(/'/g, "\\'")}', '${drug.activeSubstance ? drug.activeSubstance.replace(/'/g, "\\'") : ''}', '${drug.registrationNumber ? drug.registrationNumber.replace(/'/g, "\\'") : ''}')">
                            Использовать в рецепте
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Добавление модального окна в DOM
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHtml;
    document.body.appendChild(modalContainer);
    
    // Показ модального окна
    const modal = new bootstrap.Modal(document.getElementById('drugDetailsModal'));
    modal.show();
    
    // Удаление модального окна после закрытия
    document.getElementById('drugDetailsModal').addEventListener('hidden.bs.modal', function() {
        modalContainer.remove();
    });
}

// Использование препарата в рецепте
function useDrugInRecipe(drugName, activeSubstance, registrationNumber = '') {
    document.getElementById('drugName').value = drugName;
    document.getElementById('activeSubstance').value = activeSubstance;
    
    // Если есть поле для регистрационного номера, заполняем его
    const registrationField = document.getElementById('drugRegistrationNumber');
    if (registrationField && registrationNumber) {
        registrationField.value = registrationNumber;
    }
    
    // Закрытие модального окна
    const modal = bootstrap.Modal.getInstance(document.getElementById('drugDetailsModal'));
    if (modal) modal.hide();
    
    // Переключение на вкладку нового рецепта
    document.getElementById('new-tab').click();
    
    showAlert(`Препарат "${drugName}" добавлен в рецепт`, 'success');
}

// Загрузка последних рецептов
function loadRecentRecipes() {
    const container = document.getElementById('recentRecipes');
    container.innerHTML = '';
    
    // Берем последние 5 рецептов
    const recentRecipes = [...allRecipes]
        .sort((a, b) => new Date(b.issueDate) - new Date(a.issueDate))
        .slice(0, 5);
    
    if (recentRecipes.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-3">
                <i class="fas fa-history fa-lg mb-2"></i>
                <p>Нет сохраненных рецептов</p>
            </div>
        `;
    } else {
        recentRecipes.forEach(recipe => {
            const item = document.createElement('a');
            item.className = 'list-group-item list-group-item-action';
            item.href = '#';
            item.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${recipe.number} - ${recipe.ownerName}</h6>
                    <small>${formatDate(recipe.issueDate)}</small>
                </div>
                <p class="mb-1">${recipe.drugName}</p>
                <small>${recipe.doctorName}</small>
            `;
            item.onclick = () => viewRecipe(recipe.id);
            container.appendChild(item);
        });
    }
}

// Загрузка статуса согласий
function loadConsentStatus() {
    const container = document.getElementById('consentStatus');
    container.innerHTML = '';
    
    if (allConsents.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-3">
                <i class="fas fa-clipboard-check fa-lg mb-2"></i>
                <p>Нет сохраненных согласий</p>
            </div>
        `;
    } else {
        allConsents.forEach(consent => {
            const item = document.createElement('a');
            item.className = 'list-group-item list-group-item-action';
            item.href = '#';
            
            const statusIcon = consent.agreed ? 
                '<i class="fas fa-check-circle text-success me-2"></i>' : 
                '<i class="fas fa-times-circle text-danger me-2"></i>';
            
            item.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${statusIcon} ${consent.ownerName}</h6>
                    <small>${formatDate(consent.date)}</small>
                </div>
                <p class="mb-1">${consent.agreed ? 'Согласие получено' : 'Согласие не получено'}</p>
            `;
            container.appendChild(item);
        });
    }
}

// Инициализация автодополнения для препаратов
function initDrugAutocomplete() {
    const input = document.getElementById('drugName');
    const dropdown = document.getElementById('drugAutocomplete');
    
    if (!input || !dropdown) {
        console.error('Элементы для автодополнения не найдены');
        return;
    }
    
    // Очистка предыдущих обработчиков
    input.removeEventListener('input', handleInput);
    document.removeEventListener('click', handleClickOutside);
    input.removeEventListener('keydown', handleKeyDown);
    
    function handleInput() {
        const searchTerm = this.value.toLowerCase();
        
        if (searchTerm.length < 1) {
            dropdown.style.display = 'none';
            return;
        }
        
        // Фильтрация препаратов из всех источников
        const allAvailableDrugs = [...allDrugs, ...serverDrugs];
        
        // Удаление дубликатов по имени
        const uniqueDrugs = [];
        const seenNames = new Set();
        
        allAvailableDrugs.forEach(drug => {
            if (drug.name && !seenNames.has(drug.name.toLowerCase())) {
                seenNames.add(drug.name.toLowerCase());
                uniqueDrugs.push(drug);
            }
        });
        
        const filteredDrugs = uniqueDrugs.filter(drug => 
            (drug.name && drug.name.toLowerCase().includes(searchTerm)) ||
            (drug.activeSubstance && drug.activeSubstance.toLowerCase().includes(searchTerm))
        );
        
        if (filteredDrugs.length === 0) {
            dropdown.style.display = 'none';
            return;
        }
        
        // Отображение результатов
        dropdown.innerHTML = '';
        filteredDrugs.forEach(drug => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            item.textContent = `${drug.name} (${drug.activeSubstance || 'без вещества'})`;
            item.dataset.drugId = drug.id;
            item.dataset.drugName = drug.name;
            item.dataset.activeSubstance = drug.activeSubstance || '';
            item.dataset.registrationNumber = drug.registrationNumber || '';
            
            item.addEventListener('click', function() {
                input.value = this.dataset.drugName;
                document.getElementById('activeSubstance').value = this.dataset.activeSubstance;
                document.getElementById('drugRegistrationNumber').value = this.dataset.registrationNumber;
                dropdown.style.display = 'none';
            });
            
            dropdown.appendChild(item);
        });
        
        // Позиционирование dropdown
        const rect = input.getBoundingClientRect();
        dropdown.style.position = 'absolute';
        dropdown.style.left = rect.left + 'px';
        dropdown.style.top = (rect.bottom + window.scrollY) + 'px';
        dropdown.style.width = rect.width + 'px';
        dropdown.style.display = 'block';
        dropdown.style.zIndex = '1000';
    }
    
    function handleClickOutside(event) {
        if (!input.contains(event.target) && !dropdown.contains(event.target)) {
            dropdown.style.display = 'none';
        }
    }
    
    function handleKeyDown(event) {
        const items = dropdown.querySelectorAll('.autocomplete-item');
        let selectedIndex = -1;
        
        // Находим текущий выбранный элемент
        items.forEach((item, index) => {
            if (item.classList.contains('active')) {
                selectedIndex = index;
            }
        });
        
        if (event.key === 'ArrowDown') {
            event.preventDefault();
            selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
            updateSelectedItem(items, selectedIndex);
        } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            selectedIndex = Math.max(selectedIndex - 1, -1);
            updateSelectedItem(items, selectedIndex);
        } else if (event.key === 'Enter' && selectedIndex >= 0) {
            event.preventDefault();
            items[selectedIndex].click();
        } else if (event.key === 'Escape') {
            dropdown.style.display = 'none';
        }
    }
    
    function updateSelectedItem(items, selectedIndex) {
        items.forEach((item, index) => {
            item.classList.toggle('active', index === selectedIndex);
        });
        
        if (selectedIndex >= 0 && items[selectedIndex]) {
            items[selectedIndex].scrollIntoView({ block: 'nearest' });
        }
    }
    
    // Добавление обработчиков событий
    input.addEventListener('input', handleInput);
    document.addEventListener('click', handleClickOutside);
    input.addEventListener('keydown', handleKeyDown);
    
    console.log('Автодополнение инициализировано');
}

// Сохранение рецепта
function saveRecipe() {
    // Валидация формы
    const form = document.getElementById('recipeForm');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    // Генерация ID группы, если это первый рецепт в группе
    let groupId = localStorage.getItem('currentRecipeGroupId');
    if (!groupId) {
        groupId = 'G-' + Date.now().toString().slice(-6);
        localStorage.setItem('currentRecipeGroupId', groupId);
    }
    
    // Сбор данных
    const recipe = {
        id: generateId(allRecipes),
        number: document.getElementById('recipeNumber').value,
        issueDate: document.getElementById('issueDate').value,
        orgOGRN: document.getElementById('orgOGRN').value,
        orgName: document.getElementById('orgName').value,
        orgAddress: document.getElementById('orgAddress').value,
        ownerName: document.getElementById('ownerName').value,
        ownerAddress: document.getElementById('ownerAddress').value,
        animalType: document.getElementById('animalType').value,
        animalGender: document.getElementById('animalGender').value,
        animalAge: document.getElementById('animalAge').value,
        animalCount: parseInt(document.getElementById('animalCount').value) || 1,
        animalName: document.getElementById('animalName').value,
        drugName: document.getElementById('drugName').value,
        activeSubstance: document.getElementById('activeSubstance').value,
        dosage: document.getElementById('dosage').value,
        dose: document.getElementById('dose').value,
        frequency: document.getElementById('frequency').value,
        applicationTime: document.getElementById('applicationTime').value,
        duration: document.getElementById('duration').value,
        applicationMethod: document.getElementById('applicationMethod').value,
        feedingTime: document.getElementById('feedingTime').value,
        validityDays: parseInt(document.getElementById('validityDays').value) || 30,
        copyNumber: document.getElementById('copyNumber').value,
        urgentManufacturing: document.getElementById('urgentManufacturing').checked,
        analogDrug: document.getElementById('analogDrug').value,
        doctorName: document.getElementById('doctorName').value,
        doctorSigned: document.getElementById('doctorSigned').checked,
        groupId: groupId,
        status: 'prescribed',
        createdAt: new Date().toISOString()
    };
    
    // Добавление рецепта
    allRecipes.push(recipe);
    saveRecipes();
    
    // Показать уведомление
    showAlert('Рецепт успешно сохранен!', 'success');
    
    // Обновление интерфейса
    loadRecipes();
    loadRecentRecipes();
    generateRecipeNumber();
    
    // Переключение на вкладку журнала
    document.getElementById('journal-tab').click();
}

// Добавление еще одного рецепта для того же клиента
function addAnotherRecipe() {
    // Сохраняем текущий рецепт
    saveRecipe();
    
    // Очищаем только поля препарата и назначения
    document.getElementById('drugName').value = '';
    document.getElementById('activeSubstance').value = '';
    document.getElementById('dosage').value = '';
    document.getElementById('dose').value = '';
    document.getElementById('frequency').value = '';
    document.getElementById('applicationTime').value = '';
    document.getElementById('duration').value = '';
    document.getElementById('applicationMethod').value = '';
    document.getElementById('feedingTime').value = '';
    document.getElementById('analogDrug').value = '';
    
    // Генерируем новый номер рецепта
    generateRecipeNumber();
    
    // Обновляем предпросмотр
    updatePreview();
    
    showAlert('Готово! Теперь можно добавить еще один рецепт для этого же клиента.', 'info');
}

// Завершение группы рецептов
function finishRecipeGroup() {
    localStorage.removeItem('currentRecipeGroupId');
    showAlert('Группа рецептов завершена. Следующий рецепт будет в новой группе.', 'success');
}

// Сброс формы
function resetForm() {
    if (confirm('Вы уверены, что хотите очистить форму? Все несохраненные данные будут потеряны.')) {
        document.getElementById('recipeForm').reset();
        document.getElementById('orgOGRN').value = '1156382000774';
        document.getElementById('orgName').value = 'ООО «ВетГид»';
        document.getElementById('orgAddress').value = '445031, Самарская обл, Тольятти г, 70 лет Октября ул, дом № 60';
        document.getElementById('activeSubstance').value = '';
        generateRecipeNumber();
        updatePreview();
    }
}

// Добавление препарата
function addDrug() {
    const form = document.getElementById('addDrugForm');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const drug = {
        id: generateId(allDrugs),
        name: document.getElementById('newDrugName').value,
        activeSubstance: document.getElementById('newActiveSubstance').value,
        concentration: document.getElementById('newConcentration').value,
        unit: document.getElementById('newUnit').value,
        registrationNumber: document.getElementById('newRegistrationNumber').value,
        form: document.getElementById('newForm').value,
        manufacturer: document.getElementById('newManufacturer').value,
        shelfLife: parseInt(document.getElementById('newShelfLife').value) || 24,
        prescriptionRequired: document.getElementById('newPrescriptionRequired').checked
    };
    
    allDrugs.push(drug);
    saveDrugs();
    
    // Закрытие модального окна
    const modal = bootstrap.Modal.getInstance(document.getElementById('addDrugModal'));
    modal.hide();
    
    // Очистка формы
    form.reset();
    
    // Обновление таблицы
    loadDrugs();
    
    showAlert('Препарат успешно добавлен!', 'success');
}

// Добавление бланка
function addBlank() {
    const form = document.getElementById('addBlankForm');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const blank = {
        id: generateId(allBlanks),
        number: document.getElementById('newBlankNumber').value,
        issueDate: document.getElementById('newBlankIssueDate').value,
        doctor: document.getElementById('newBlankDoctor').value,
        recipeNumber: document.getElementById('newBlankRecipeNumber').value,
        status: document.getElementById('newBlankStatus').value
    };
    
    allBlanks.push(blank);
    saveBlanks();
    
    // Закрытие модального окна
    const modal = bootstrap.Modal.getInstance(document.getElementById('addBlankModal'));
    modal.hide();
    
    // Очистка формы
    form.reset();
    
    // Обновление таблицы
    loadBlanks();
    
    showAlert('Бланк успешно добавлен!', 'success');
}

// Сохранение согласия
function saveConsent() {
    const ownerName = document.getElementById('consentOwnerName').value;
    const date = document.getElementById('consentDate').value;
    const agreed = document.getElementById('consentAgreed').checked;
    
    if (!ownerName) {
        showAlert('Пожалуйста, укажите ФИО владельца', 'warning');
        return;
    }
    
    const consent = {
        id: generateId(allConsents),
        ownerName: ownerName,
        date: date,
        agreed: agreed,
        createdAt: new Date().toISOString()
    };
    
    allConsents.push(consent);
    saveConsents();
    
    showAlert('Согласие успешно сохранено!', 'success');
    loadConsentStatus();
}

// Печать согласия
function printConsent() {
    // Проверка заполнения обязательных полей
    const ownerName = document.getElementById('consentOwnerName').value;
    if (!ownerName.trim()) {
        showAlert('Пожалуйста, укажите ФИО владельца', 'warning');
        document.getElementById('consentOwnerName').focus();
        return;
    }
    
    // Сохраняем согласие перед печатью
    saveConsent();
    
    // Печать
    window.print();
}

// Выгрузка согласия в PDF
function downloadConsentPDF() {
    const ownerName = document.getElementById('consentOwnerName').value;
    const date = document.getElementById('consentDate').value;
    const agreed = document.getElementById('consentAgreed').checked;
    
    if (!ownerName.trim()) {
        showAlert('Пожалуйста, укажите ФИО владельца', 'warning');
        document.getElementById('consentOwnerName').focus();
        return;
    }
    
    // Сохраняем согласие
    saveConsent();
    
    try {
        // Проверяем, доступны ли библиотеки
        if (typeof window.jspdf === 'undefined') {
            showAlert('Ошибка: Библиотека PDF не загружена. Пожалуйста, обновите страницу.', 'error');
            console.error('jsPDF не загружена');
            return;
        }
        
        if (typeof html2canvas === 'undefined') {
            showAlert('Ошибка: Библиотека html2canvas не загружена. Пожалуйста, обновите страницу.', 'error');
            console.error('html2canvas не загружена');
            return;
        }
        
        // Создаем временный элемент для отображения согласия
        const tempDiv = document.createElement('div');
        tempDiv.style.cssText = `
            position: absolute;
            left: -10000px;
            top: -10000px;
            width: 210mm;
            height: 297mm;
            padding: 20mm;
            font-family: Arial, sans-serif;
            font-size: 12pt;
            line-height: 1.5;
            background: white;
            color: black;
        `;
        
        const consentHtml = `
            <div style="text-align: center; margin-bottom: 20mm;">
                <h1 style="font-size: 18pt; margin-bottom: 10mm;">СОГЛАСИЕ НА ЛЕЧЕНИЕ И ОТВЕТСТВЕННОСТЬ</h1>
            </div>
            <div style="margin-bottom: 10mm;">
                <p>Я, нижеподписавшийся(аяся), владелец животного (или законный представитель), подтверждаю, что:</p>
                <ol style="margin-left: 20mm;">
                    <li>Мною получена полная консультация ветеринарного врача/фельдшера о состоянии здоровья моего животного.</li>
                    <li>Мне разъяснены риски, возможные побочные эффекты и правила применения назначенного лекарственного препарата.</li>
                    <li>Я обязуюсь строго соблюдать дозировку, кратность и длительность применения препарата в соответствии с рецептом.</li>
                    <li>Я несу ответственность за хранение препарата в недоступном для детей и животных месте.</li>
                    <li>Я уведомлен(а), что самовольное изменение дозировки или преждевременное прекращение лечения может нанести вред здоровью животного.</li>
                    <li>Я согласен(а) на обработку моих персональных данных.</li>
                </ol>
            </div>
            <div style="margin-top: 20mm;">
                <p><strong>ФИО владельца:</strong> ${ownerName}</p>
                <p><strong>Дата:</strong> ${formatDate(date)}</p>
                <p><strong>Согласие получено:</strong> ${agreed ? 'Да' : 'Нет'}</p>
            </div>
            <div style="margin-top: 30mm;">
                <p>Подпись владельца: ____________________</p>
            </div>
        `;
        
        tempDiv.innerHTML = consentHtml;
        document.body.appendChild(tempDiv);
        
        // Используем html2canvas для создания изображения
        html2canvas(tempDiv, {
            scale: 2,
            useCORS: true,
            logging: false,
            backgroundColor: '#FFFFFF'
        }).then(canvas => {
            const imgData = canvas.toDataURL('image/png');
            
            // Создание PDF
            const { jsPDF } = window.jspdf;
            const pdf = new jsPDF('p', 'mm', 'a4');
            const imgWidth = 190;
            const imgHeight = canvas.height * imgWidth / canvas.width;
            
            pdf.addImage(imgData, 'PNG', 10, 10, imgWidth, imgHeight);
            
            // Сохраняем PDF
            const fileName = `Согласие_${ownerName.replace(/[^a-zA-Zа-яА-Я0-9]/g, '_')}_${date}.pdf`;
            pdf.save(fileName);
            
            // Удаляем временный элемент
            document.body.removeChild(tempDiv);
            
            showAlert('Согласие успешно выгружено в PDF!', 'success');
            console.log('PDF успешно создан:', fileName);
        }).catch(error => {
            console.error('Ошибка создания изображения для PDF:', error);
            showAlert('Ошибка при создании PDF. Пожалуйста, попробуйте еще раз.', 'error');
            if (tempDiv.parentNode) {
                document.body.removeChild(tempDiv);
            }
        });
        
    } catch (error) {
        console.error('Ошибка создания PDF:', error);
        showAlert(`Ошибка создания PDF: ${error.message}. Пожалуйста, попробуйте еще раз.`, 'error');
    }
}

// Генерация PDF
function generatePDF() {
    // Проверка заполнения обязательных полей
    const requiredFields = ['ownerName', 'drugName', 'doctorName'];
    for (const fieldId of requiredFields) {
        const field = document.getElementById(fieldId);
        if (!field.value.trim()) {
            showAlert(`Пожалуйста, заполните поле: ${field.previousElementSibling.textContent}`, 'warning');
            field.focus();
            return;
        }
    }
    
    // Используем html2canvas для создания изображения
    const element = document.getElementById('printPreview');
    
    html2canvas(element, {
        scale: 2,
        useCORS: true,
        logging: false
    }).then(canvas => {
        const imgData = canvas.toDataURL('image/png');
        
        // Создание PDF
        const { jsPDF } = window.jspdf;
        const pdf = new jsPDF('p', 'mm', 'a4');
        const imgWidth = 190;
        const imgHeight = canvas.height * imgWidth / canvas.width;
        
        pdf.addImage(imgData, 'PNG', 10, 10, imgWidth, imgHeight);
        pdf.save(`Рецепт_${document.getElementById('recipeNumber').value}.pdf`);
        
        showAlert('PDF успешно сгенерирован!', 'success');
    }).catch(error => {
        console.error('Ошибка генерации PDF:', error);
        showAlert('Ошибка при генерации PDF. Пожалуйста, попробуйте еще раз.', 'error');
    });
}

// Экспорт рецептов в Excel
function exportToExcel() {
    if (allRecipes.length === 0) {
        showAlert('Нет данных рецептов для экспорта', 'warning');
        return;
    }
    
    try {
        // Проверяем, доступна ли библиотека XLSX
        if (typeof XLSX === 'undefined') {
            showAlert('Ошибка: Библиотека Excel не загружена. Пожалуйста, обновите страницу.', 'error');
            console.error('XLSX не загружена');
            return;
        }
        
        // Подготовка данных
        const data = allRecipes.map(recipe => ({
            '№ рецепта': recipe.number,
            'Дата выписки': formatDate(recipe.issueDate),
            'ФИО владельца': recipe.ownerName,
            'Вид животного': recipe.animalType,
            'Кличка': recipe.animalName,
            'Препарат': recipe.drugName,
            'Действующее вещество': recipe.activeSubstance,
            'Врач': recipe.doctorName,
            'Статус': getStatusText(recipe.status)
        }));
        
        // Создание рабочей книги
        const ws = XLSX.utils.json_to_sheet(data);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'Рецепты');
        
        // Сохранение файла
        const fileName = `Рецепты_${new Date().toISOString().split('T')[0]}.xlsx`;
        XLSX.writeFile(wb, fileName);
        
        showAlert('Данные рецептов успешно экспортированы в Excel!', 'success');
    } catch (error) {
        console.error('Ошибка экспорта в Excel:', error);
        showAlert(`Ошибка экспорта в Excel: ${error.message}. Пожалуйста, попробуйте еще раз.`, 'error');
    }
}

// Экспорт согласий в Excel
function exportConsentsToExcel() {
    if (allConsents.length === 0) {
        showAlert('Нет данных согласий для экспорта', 'warning');
        return;
    }
    
    try {
        // Проверяем, доступна ли библиотека XLSX
        if (typeof XLSX === 'undefined') {
            showAlert('Ошибка: Библиотека Excel не загружена. Пожалуйста, обновите страницу.', 'error');
            console.error('XLSX не загружена');
            return;
        }
        
        // Подготовка данных
        const data = allConsents.map(consent => ({
            'ФИО владельца': consent.ownerName,
            'Дата': formatDate(consent.date),
            'Согласие получено': consent.agreed ? 'Да' : 'Нет',
            'Дата создания': formatDate(consent.createdAt)
        }));
        
        // Создание рабочей книги
        const ws = XLSX.utils.json_to_sheet(data);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'Согласия');
        
        // Сохранение файла
        const fileName = `Согласия_${new Date().toISOString().split('T')[0]}.xlsx`;
        XLSX.writeFile(wb, fileName);
        
        showAlert('Данные согласий успешно экспортированы в Excel!', 'success');
    } catch (error) {
        console.error('Ошибка экспорта согласий в Excel:', error);
        showAlert(`Ошибка экспорта согласий в Excel: ${error.message}. Пожалуйста, попробуйте еще раз.`, 'error');
    }
}

// Вспомогательные функции
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU');
}

function getStatusText(status) {
    switch (status) {
        case 'prescribed': return 'Выписан';
        case 'dispensed': return 'Отпущен';
        case 'expired': return 'Просрочен';
        default: return status;
    }
}

function updatePagination(elementId, currentPage, totalPages, callback) {
    const pagination = document.getElementById(elementId);
    pagination.innerHTML = '';
    
    if (totalPages <= 1) return;
    
    // Кнопка "Назад"
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `<a class="page-link" href="#">Назад</a>`;
    prevLi.onclick = (e) => {
        e.preventDefault();
        if (currentPage > 1) callback(currentPage - 1);
    };
    pagination.appendChild(prevLi);
    
    // Номера страниц
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, startPage + 4);
    
    for (let i = startPage; i <= endPage; i++) {
        const pageLi = document.createElement('li');
        pageLi.className = `page-item ${i === currentPage ? 'active' : ''}`;
        pageLi.innerHTML = `<a class="page-link" href="#">${i}</a>`;
        pageLi.onclick = (e) => {
            e.preventDefault();
            callback(i);
        };
        pagination.appendChild(pageLi);
    }
    
    // Кнопка "Вперед"
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    nextLi.innerHTML = `<a class="page-link" href="#">Вперед</a>`;
    nextLi.onclick = (e) => {
        e.preventDefault();
        if (currentPage < totalPages) callback(currentPage + 1);
    };
    pagination.appendChild(nextLi);
}

function showAlert(message, type = 'info') {
    // Создание уведомления
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alert.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);
    
    // Автоматическое скрытие
    setTimeout(() => {
        if (alert.parentNode) {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 300);
        }
    }, 5000);
}

// Функции для редактирования и удаления (заглушки)
function editRecipe(id) {
    showAlert('Функция редактирования в разработке', 'info');
}

function deleteRecipe(id) {
    if (confirm('Вы уверены, что хотите удалить этот рецепт?')) {
        allRecipes = allRecipes.filter(recipe => recipe.id !== id);
        saveRecipes();
        loadRecipes();
        showAlert('Рецепт успешно удален', 'success');
    }
}

function editDrug(id) {
    showAlert('Функция редактирования препарата в разработке', 'info');
}

function deleteDrug(id) {
    if (confirm('Вы уверены, что хотите удалить этот препарат?')) {
        allDrugs = allDrugs.filter(drug => drug.id !== id);
        saveDrugs();
        loadDrugs();
        showAlert('Препарат успешно удален', 'success');
    }
}

function editBlank(id) {
    showAlert('Функция редактирования бланка в разработке', 'info');
}

function deleteBlank(id) {
    if (confirm('Вы уверены, что хотите удалить этот бланк?')) {
        allBlanks = allBlanks.filter(blank => blank.id !== id);
        saveBlanks();
        loadBlanks();
        showAlert('Бланк успешно удален', 'success');
    }
}

function viewRecipe(id) {
    showAlert('Функция просмотра рецепта в разработке', 'info');
}

function printRecipe(id) {
    showAlert('Функция печати рецепта в разработке', 'info');
}

// Импорт препаратов из файла
function importDrugs() {
    const fileInput = document.getElementById('drugsFile');
    const progressBar = document.getElementById('importProgress');
    const resultDiv = document.getElementById('importResult');
    
    if (!fileInput.files.length) {
        showAlert('Пожалуйста, выберите файл для импорта', 'warning');
        return;
    }
    
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    // Показать прогресс
    progressBar.style.display = 'block';
    progressBar.querySelector('.progress-bar').style.width = '30%';
    
    // Отправить запрос на сервер
    fetch('/api/drugs/import', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            progressBar.querySelector('.progress-bar').style.width = '100%';
            
            // Показать результат
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>
                    <strong>Импорт успешно завершен!</strong><br>
                    Обработано препаратов: ${data.processed}<br>
                    Сохранено в базу: ${data.saved}
                </div>
            `;
            resultDiv.style.display = 'block';
            
            // Обновить список препаратов
            setTimeout(() => {
                loadDrugs();
                // Закрыть модальное окно через 3 секунды
                setTimeout(() => {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('importDrugsModal'));
                    modal.hide();
                    // Сбросить форму
                    document.getElementById('importDrugsForm').reset();
                    progressBar.style.display = 'none';
                    resultDiv.style.display = 'none';
                    progressBar.querySelector('.progress-bar').style.width = '0%';
                }, 3000);
            }, 1000);
            
            showAlert('Препараты успешно импортированы!', 'success');
        } else {
            progressBar.style.display = 'none';
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    <strong>Ошибка импорта:</strong> ${data.error}
                </div>
            `;
            resultDiv.style.display = 'block';
            showAlert(`Ошибка импорта: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        progressBar.style.display = 'none';
        resultDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                <strong>Ошибка соединения:</strong> ${error.message}
            </div>
        `;
        resultDiv.style.display = 'block';
        showAlert(`Ошибка соединения: ${error.message}`, 'error');
    });
}

// Загрузка препаратов из сервера
function loadDrugsFromServer() {
    console.log('Загрузка препаратов с сервера...');
    fetch('/api/drugs/list')
    .then(response => {
        console.log('Ответ от сервера получен:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Данные от сервера:', data);
        if (data.drugs && data.drugs.length > 0) {
            console.log(`Получено ${data.drugs.length} препаратов с сервера`);
            // Обновить локальный список препаратов
            allDrugs = data.drugs.map(drug => ({
                id: generateId(allDrugs),
                name: drug.name,
                activeSubstance: drug.activeSubstance,
                registrationNumber: drug.registrationNumber,
                form: drug.form,
                prescriptionRequired: drug.prescriptionRequired,
                concentration: drug.concentration,
                unit: drug.unit,
                manufacturer: drug.manufacturer,
                shelfLife: drug.shelfLife
            }));
            
            // Сохранить в localStorage
            saveDrugs();
            
            // Обновить интерфейс
            loadDrugs();
            console.log('Препараты загружены и отображены');
        } else {
            console.log('Нет данных с сервера, загружаем из CSV файла');
            // Если нет данных с сервера, загрузить из CSV файла
            loadDrugsFromCSV();
        }
    })
    .catch(error => {
        console.error('Ошибка загрузки препаратов с сервера:', error);
        console.log('Загружаем препараты из CSV файла');
        // Загрузить из CSV файла при ошибке
        loadDrugsFromCSV();
    });
}

// Загрузка препаратов из CSV файла
function loadDrugsFromCSV() {
    console.log('Загрузка препаратов из CSV файла...');
    fetch('/static/test_drugs.csv')
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.text();
    })
    .then(csvText => {
        // Парсинг CSV
        const lines = csvText.split('\n');
        const headers = lines[0].split(',');
        
        const drugs = [];
        for (let i = 1; i < lines.length; i++) {
            if (lines[i].trim() === '') continue;
            
            const values = lines[i].split(',');
            if (values.length >= 6) {
                const drug = {
                    id: generateId(drugs),
                    name: values[0]?.trim() || '',
                    registrationNumber: values[1]?.trim() || '',
                    activeSubstance: values[2]?.trim() || '',
                    manufacturer: values[3]?.trim() || '',
                    form: mapFormToInternal(values[4]?.trim() || ''),
                    prescriptionRequired: values[5]?.trim()?.toLowerCase().includes('рецепт') || false
                };
                
                drugs.push(drug);
            }
        }
        
        if (drugs.length > 0) {
            console.log(`Загружено ${drugs.length} препаратов из CSV`);
            allDrugs = drugs;
            saveDrugs();
            loadDrugs();
            // Инициализировать автодополнение после загрузки препаратов
            setTimeout(() => {
                initDrugAutocomplete();
                console.log('Автодополнение инициализировано после загрузки CSV');
            }, 100);
        } else {
            console.log('Нет данных в CSV, используем препараты по умолчанию');
            // Использовать препараты по умолчанию
            allDrugs = getDefaultDrugs();
            saveDrugs();
            loadDrugs();
            setTimeout(() => {
                initDrugAutocomplete();
                console.log('Автодополнение инициализировано с препаратами по умолчанию');
            }, 100);
        }
    })
    .catch(error => {
        console.error('Ошибка загрузки CSV файла:', error);
        console.log('Используем препараты по умолчанию');
        // Использовать препараты по умолчанию
        allDrugs = getDefaultDrugs();
        saveDrugs();
        loadDrugs();
        setTimeout(() => {
            initDrugAutocomplete();
            console.log('Автодополнение инициализировано с препаратами по умолчанию после ошибки');
        }, 100);
    });
}

// Преобразование формы выпуска из CSV во внутренний формат
function mapFormToInternal(form) {
    const formMap = {
        'Таблетки': 'tablets',
        'Раствор для инъекций': 'injections',
        'Паста для приема внутрь': 'suspension',
        'Лиофилизат для приготовления раствора': 'solution',
        'Капли': 'drops',
        'Мазь': 'ointment',
        'Капсулы': 'capsules',
        'Порошок': 'powder'
    };
    
    return formMap[form] || 'other';
}

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', function() {
    initData();
    // Загрузить препараты с сервера при старте
    loadDrugsFromServer();
    
    // Добавление обработчиков событий для поиска
    setupSearchHandlers();
    
    // Инициализация автодополнения после загрузки данных
    initializeAutocompleteWithRetry();
});

// Инициализация автодополнения с повторными попытками
function initializeAutocompleteWithRetry() {
    let retryCount = 0;
    const maxRetries = 5;
    
    function tryInitialize() {
        console.log(`Попытка инициализации автодополнения (попытка ${retryCount + 1}/${maxRetries})`);
        console.log('allDrugs:', allDrugs.length, 'serverDrugs:', serverDrugs.length);
        
        // Проверяем, есть ли препараты для автодополнения
        const totalDrugs = allDrugs.length + serverDrugs.length;
        
        if (totalDrugs > 0) {
            initDrugAutocomplete();
            console.log('Автодополнение инициализировано с', totalDrugs, 'препаратами');
            showAlert('Автодополнение препаратов готово к работе', 'success');
        } else if (retryCount < maxRetries) {
            retryCount++;
            console.log('Нет препаратов, повторная попытка через 1 секунду...');
            setTimeout(tryInitialize, 1000);
        } else {
            console.log('Не удалось загрузить препараты для автодополнения');
            showAlert('Не удалось загрузить список препаратов. Пожалуйста, обновите страницу.', 'warning');
        }
    }
    
    // Первая попытка через 500 мс
    setTimeout(tryInitialize, 500);
}

// Настройка обработчиков событий для поиска
function setupSearchHandlers() {
    // Поиск в справочнике препаратов
    const searchDrugsInput = document.getElementById('searchDrugs');
    if (searchDrugsInput) {
        let searchDrugsTimeout;
        searchDrugsInput.addEventListener('input', function() {
            clearTimeout(searchDrugsTimeout);
            searchDrugsTimeout = setTimeout(() => {
                loadDrugs(1);
            }, 300); // Задержка 300 мс для предотвращения частых запросов
        });
    }
    
    // Поиск в реестре препаратов
    const searchRegistryInput = document.getElementById('searchRegistry');
    if (searchRegistryInput) {
        let searchRegistryTimeout;
        searchRegistryInput.addEventListener('input', function() {
            clearTimeout(searchRegistryTimeout);
            searchRegistryTimeout = setTimeout(() => {
                loadRegistry(1);
            }, 500); // Большая задержка для реестра, так как он может быть большим
        });
    }
    
    // Поиск в журнале рецептов
    const searchRecipesInput = document.getElementById('searchRecipes');
    if (searchRecipesInput) {
        let searchRecipesTimeout;
        searchRecipesInput.addEventListener('input', function() {
            clearTimeout(searchRecipesTimeout);
            searchRecipesTimeout = setTimeout(() => {
                loadRecipes(1);
            }, 300);
        });
    }
}
