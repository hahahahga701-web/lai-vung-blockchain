// Lai Vung Trace Network - Client Logic

// ============= DRAFT DATA MANAGEMENT =============
class FormDraftManager {
    constructor(formType) {
        this.formType = formType;
        this.storageKey = `draft_${formType}`;
    }

    save(formData) {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify({
                data: formData,
                timestamp: new Date().toISOString()
            }));
            console.log(`✓ Lưu nháp ${this.formType} thành công`);
        } catch (e) {
            console.error(`Lỗi lưu nháp: ${e.message}`);
        }
    }

    load() {
        try {
            const item = localStorage.getItem(this.storageKey);
            if (item) {
                const { data, timestamp } = JSON.parse(item);
                console.log(`✓ Tải nháp ${this.formType} (${new Date(timestamp).toLocaleString('vi-VN')})`);
                return data;
            }
            return null;
        } catch (e) {
            console.error(`Lỗi tải nháp: ${e.message}`);
            return null;
        }
    }

    clear() {
        try {
            localStorage.removeItem(this.storageKey);
            console.log(`✓ Xóa nháp ${this.formType}`);
        } catch (e) {
            console.error(`Lỗi xóa nháp: ${e.message}`);
        }
    }

    exists() {
        return localStorage.getItem(this.storageKey) !== null;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // State management
    let activeLotId = null;
    let availableLots = [];
    let farmerDraftManager = new FormDraftManager("farmer");
    let transporterDraftManager = new FormDraftManager("transporter");
    let distributorDraftManager = new FormDraftManager("distributor");
    
    // ============= CYBERPUNK SUCCESS MODAL =============
    function showSuccessModal({ title, subtitle, lotId, time, status, onViewDetails, onContinue }) {
        const overlay = document.getElementById("cyber-success-modal-overlay");
        const titleEl = document.getElementById("cyber-modal-title");
        const subtitleEl = document.getElementById("cyber-modal-subtitle");
        const lotIdEl = document.getElementById("cyber-modal-lot-id");
        const timeEl = document.getElementById("cyber-modal-time");
        const statusEl = document.getElementById("cyber-modal-status");
        
        const closeBtn = document.getElementById("cyber-modal-close-btn");
        const viewBtn = document.getElementById("cyber-modal-btn-view");
        const continueBtn = document.getElementById("cyber-modal-btn-continue");
        
        if (title) titleEl.innerText = title;
        if (subtitle) subtitleEl.innerHTML = subtitle;
        if (lotId) lotIdEl.innerText = lotId;
        
        if (time) {
            timeEl.innerText = time;
        } else {
            const now = new Date();
            let hours = now.getHours();
            let minutes = now.getMinutes();
            let ampm = hours >= 12 ? 'PM' : 'AM';
            hours = hours % 12;
            hours = hours ? hours : 12;
            minutes = minutes < 10 ? '0' + minutes : minutes;
            let timeString = hours + ':' + minutes + ' ' + ampm;
            
            let day = now.getDate();
            let month = now.getMonth() + 1;
            let year = now.getFullYear();
            day = day < 10 ? '0' + day : day;
            month = month < 10 ? '0' + month : month;
            let dateString = day + '/' + month + '/' + year;
            
            timeEl.innerText = `${timeString} - ${dateString}`;
        }
        
        if (status) {
            statusEl.innerHTML = `${status} <i class="fa-solid fa-circle-check"></i>`;
        } else {
            statusEl.innerHTML = `Đã xác thực trên Blockchain <i class="fa-solid fa-circle-check"></i>`;
        }
        
        const hideModal = () => {
            overlay.classList.remove("active");
            closeBtn.onclick = null;
            viewBtn.onclick = null;
            continueBtn.onclick = null;
        };
        
        closeBtn.onclick = hideModal;
        
        viewBtn.onclick = () => {
            hideModal();
            if (onViewDetails) onViewDetails();
        };
        
        continueBtn.onclick = () => {
            hideModal();
            if (onContinue) onContinue();
        };
        
        overlay.classList.add("active");
    }
    
    // ============= CYBERPUNK FAILURE MODAL =============
    function showFailureModal(title, subtitle, errorDetails, onContinue) {
        const overlay = document.getElementById("cyber-failure-modal-overlay");
        const titleEl = document.getElementById("cyber-failure-modal-title");
        const subtitleEl = document.getElementById("cyber-failure-modal-subtitle");
        const detailsEl = document.getElementById("cyber-failure-modal-details-val");
        
        const closeBtn = document.getElementById("cyber-failure-modal-close-btn");
        const continueBtn = document.getElementById("cyber-failure-modal-btn-close");
        
        if (title) titleEl.innerText = title;
        if (subtitle) subtitleEl.innerHTML = subtitle;
        if (errorDetails) {
            detailsEl.innerText = errorDetails;
        } else {
            detailsEl.innerText = "Đã xảy ra lỗi không xác định.";
        }
        
        const hideModal = () => {
            overlay.classList.remove("active");
            closeBtn.onclick = null;
            continueBtn.onclick = null;
        };
        
        closeBtn.onclick = hideModal;
        continueBtn.onclick = () => {
            hideModal();
            if (onContinue) onContinue();
        };
        
        overlay.classList.add("active");
    }
    
    // ============= UTILITY TO PARSE AND SHOW API ERRORS =============
    function parseAndShowAPIError(defaultTitle, data) {
        let errorMessage = "Đã xảy ra lỗi không xác định.";
        let errorDetailString = "";

        if (data) {
            if (data.detail !== undefined) {
                if (typeof data.detail === "string") {
                    errorMessage = data.detail;
                } else if (Array.isArray(data.detail)) {
                    errorMessage = "Dữ liệu đầu vào không đúng cấu hình yêu cầu.";
                    errorDetailString = data.detail.map(err => {
                        const field = err.loc ? err.loc.join('.') : 'trường';
                        return `${field}: ${err.msg}`;
                    }).join("\n• ");
                } else if (typeof data.detail === "object" && data.detail !== null) {
                    errorMessage = data.detail.message || "Dữ liệu không hợp lệ";
                    if (data.detail.errors && Array.isArray(data.detail.errors)) {
                        errorDetailString = data.detail.errors.join("\n• ");
                    }
                }
            } else {
                if (data.message) {
                    errorMessage = data.message;
                }
                if (data.errors && Array.isArray(data.errors)) {
                    errorDetailString = data.errors.join("\n• ");
                }
            }
        }

        if (errorDetailString) {
            showFailureModal(defaultTitle, errorMessage, errorDetailString);
        } else {
            showFailureModal(defaultTitle, errorMessage, (data && data.message) || "Kiểm tra lại kết nối hoặc dữ liệu.");
        }
    }

    
    // ============= LIGHT/DARK MODE TOGGLE =============
    const themeToggleBtn = document.getElementById("theme-toggle-btn");
    const themeText = document.getElementById("theme-text");
    const htmlElement = document.documentElement;
    
    // Load saved theme preference
    const savedTheme = localStorage.getItem("theme-preference") || "dark";
    if (savedTheme === "light") {
        htmlElement.classList.add("light-mode");
        themeText.textContent = "Light";
        themeToggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i> <span id="theme-text">Light</span>';
    }
    
    // Toggle theme on button click
    themeToggleBtn.addEventListener("click", () => {
        const isLightMode = htmlElement.classList.toggle("light-mode");
        localStorage.setItem("theme-preference", isLightMode ? "light" : "dark");
        
        if (isLightMode) {
            themeText.textContent = "Light";
            themeToggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i> <span id="theme-text">Light</span>';
        } else {
            themeText.textContent = "Dark";
            themeToggleBtn.innerHTML = '<i class="fa-solid fa-moon"></i> <span id="theme-text">Dark</span>';
        }
    });
    
    // ============= MOBILE HAMBURGER MENU =============
    const mobileMenuToggle = document.getElementById("mobile-menu-toggle");
    const mainNav = document.getElementById("main-nav");
    const navButtons = document.querySelectorAll(".nav-btn");
    
    // Initialize menu as hidden on mobile (add mobile-hidden class by default on small screens)
    function initializeMobileMenu() {
        if (window.innerWidth <= 768 && mainNav && !mainNav.classList.contains("mobile-hidden")) {
            mainNav.classList.add("mobile-hidden");
        }
    }
    
    // Call on page load
    initializeMobileMenu();
    
    // Also handle window resize
    window.addEventListener("resize", () => {
        if (window.innerWidth > 768 && mainNav) {
            // On desktop, remove mobile-hidden to show menu
            mainNav.classList.remove("mobile-hidden");
        } else if (window.innerWidth <= 768 && mainNav && !mainNav.classList.contains("mobile-hidden")) {
            // On mobile, add mobile-hidden to hide menu
            mainNav.classList.add("mobile-hidden");
        }
    });
    
    // Mobile menu toggle functionality
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener("click", () => {
            if (mainNav) {
                mainNav.classList.toggle("mobile-hidden");
                mobileMenuToggle.classList.toggle("active");
            }
        });
    }
    
    // Close mobile menu when clicking on a nav button (mobile only)
    navButtons.forEach(btn => {
        if (btn.id !== "theme-toggle-btn") {
            btn.addEventListener("click", () => {
                if (window.innerWidth <= 768 && mainNav) {
                    mainNav.classList.add("mobile-hidden");
                    if (mobileMenuToggle) {
                        mobileMenuToggle.classList.remove("active");
                    }
                }
            });
        }
    });
    
    // Close mobile menu when clicking outside (mobile only)
    document.addEventListener("click", (e) => {
        if (window.innerWidth <= 768 && mobileMenuToggle && mainNav && 
            !mobileMenuToggle.contains(e.target) && 
            !mainNav.contains(e.target)) {
            mainNav.classList.add("mobile-hidden");
            mobileMenuToggle.classList.remove("active");
        }
    });

    // Initialize tab state: Ensure farmer tab is active on page load
    // This also fixes the issue when theme is changed
    const initializeTab = () => {
        const allNavButtons = document.querySelectorAll(".nav-btn");
        const tabContents = document.querySelectorAll(".tab-content");
        
        // Activate farmer tab
        allNavButtons.forEach(btn => {
            if (btn.getAttribute("data-tab") === "farmer") {
                btn.classList.add("active");
            } else {
                btn.classList.remove("active");
            }
        });
        
        tabContents.forEach(tab => {
            if (tab.id === "farmer") {
                tab.classList.add("active");
            } else {
                tab.classList.remove("active");
            }
        });
    };
    
    // Call initialization after a brief delay to ensure DOM is ready
    // Also ensures theme has been applied before initializing tabs
    setTimeout(initializeTab, 50);
    
    // ============= AUTOCOMPLETE FUNCTIONALITY =============
    async function setupAutocomplete(inputId, suggestionsContainerId, type) {
        const input = document.getElementById(inputId);
        const suggestionsContainer = document.getElementById(suggestionsContainerId);
        
        if (!input) return;
        
        input.addEventListener("input", async (e) => {
            const query = e.target.value.trim();
            
            if (query.length < 1) {
                suggestionsContainer.style.display = "none";
                return;
            }
            
            try {
                const endpoint = type === "fertilizer" 
                    ? `/api/vietgap/fertilizers/search?q=${encodeURIComponent(query)}`
                    : `/api/vietgap/pesticides/search?q=${encodeURIComponent(query)}`;
                    
                const response = await fetch(endpoint);
                const data = await response.json();
                
                if (data.results && data.results.length > 0) {
                    suggestionsContainer.innerHTML = data.results
                        .map(item => `
                            <div class="suggestion-item" data-value="${item.name}">
                                <span style="color: var(--accent-orange); font-weight: 500; font-size: 0.85rem;">${item.category}</span><br>
                                ${item.name}
                            </div>
                        `).join("");
                    
                    suggestionsContainer.style.display = "block";
                    
                    // Add click listeners to suggestions
                    suggestionsContainer.querySelectorAll(".suggestion-item").forEach(item => {
                        item.addEventListener("click", () => {
                            input.value = item.dataset.value;
                            suggestionsContainer.style.display = "none";
                        });
                    });
                } else {
                    suggestionsContainer.innerHTML = '<div class="suggestion-item" style="color: var(--text-muted); padding: 12px 16px;">Không tìm thấy kết quả</div>';
                    suggestionsContainer.style.display = "block";
                }
            } catch (error) {
                console.error("Autocomplete error:", error);
            }
        });
        
        // Hide suggestions when clicking outside
        document.addEventListener("click", (e) => {
            if (e.target !== input) {
                suggestionsContainer.style.display = "none";
            }
        });
    }
    
    // Initialize autocomplete for fertilizers and pesticides
    setupAutocomplete("farmer-fertilizer", "farmer-fertilizer-suggestions", "fertilizer");
    setupAutocomplete("farmer-pesticide", "farmer-pesticide-suggestions", "pesticide");
    
    // ============= PHI (PRE-HARVEST INTERVAL) CALCULATION =============
    function calculatePHI() {
        const lastSprayInput = document.getElementById("farmer-last-spray-date");
        const harvestInput = document.getElementById("farmer-harvest-date");
        const phiAlert = document.getElementById("farmer-phi-alert");
        const phiStatus = document.getElementById("farmer-phi-status");
        const phiMessage = document.getElementById("farmer-phi-message");
        
        if (!lastSprayInput.value || !harvestInput.value) {
            phiAlert.style.display = "none";
            return;
        }
        
        const lastSpray = new Date(lastSprayInput.value);
        const harvest = new Date(harvestInput.value);
        const daysElapsed = Math.floor((harvest - lastSpray) / (1000 * 60 * 60 * 24));
        const requiredPHI = 14; // Standard PHI for most pesticides
        const daysRemaining = requiredPHI - daysElapsed;
        const isSafe = daysElapsed >= requiredPHI;
        
        phiStatus.textContent = isSafe 
            ? "✅ AN TOÀN - Đủ thời gian cách ly thuốc BVTV" 
            : `⚠️ CHƯA AN TOÀN - Vui lòng chờ ${daysRemaining} ngày`;
        phiMessage.textContent = isSafe 
            ? `Đã ${daysElapsed} ngày từ lần phun cuối. Đủ điều kiện hái vào ${harvestInput.value}`
            : `Đã ${daysElapsed} ngày, còn cần ${daysRemaining} ngày nữa mới an toàn`;
        
        phiAlert.style.display = "block";
    }
    
    // Attach PHI calculation to date inputs
    const lastSprayInput = document.getElementById("farmer-last-spray-date");
    const harvestInput = document.getElementById("farmer-harvest-date");
    if (lastSprayInput) lastSprayInput.addEventListener("change", calculatePHI);
    if (harvestInput) harvestInput.addEventListener("change", calculatePHI);
    
    // ============= WEIGHT LOSS CALCULATION FOR LOGISTICS =============
    function calculateWeightLoss() {
        const pickupWeight = document.getElementById("trans-weight-pickup").value;
        const deliveryWeight = document.getElementById("trans-weight-delivery").value;
        const lossInfo = document.getElementById("trans-weight-loss-info");
        
        if (pickupWeight && deliveryWeight) {
            const loss = parseFloat(pickupWeight) - parseFloat(deliveryWeight);
            const lossPercent = ((loss / pickupWeight) * 100).toFixed(2);
            
            document.getElementById("trans-weight-loss-value").textContent = loss.toFixed(2);
            document.getElementById("trans-weight-loss-pct").textContent = lossPercent;
            lossInfo.style.display = "block";
        } else {
            lossInfo.style.display = "none";
        }
    }
    
    const pickupWeightInput = document.getElementById("trans-weight-pickup");
    const deliveryWeightInput = document.getElementById("trans-weight-delivery");
    if (pickupWeightInput) pickupWeightInput.addEventListener("change", calculateWeightLoss);
    if (deliveryWeightInput) deliveryWeightInput.addEventListener("change", calculateWeightLoss);
    
    // ============= SHELF LIFE CALCULATION =============
    document.getElementById("btn-calculate-shelf-life")?.addEventListener("click", async (e) => {
        e.preventDefault();
        
        const harvestDate = document.getElementById("farmer-harvest-date")?.value;
        const warehouseDate = document.getElementById("dist-warehouse-date")?.value;
        const storageCondition = document.getElementById("dist-storage")?.value;
        
        if (!harvestDate || !warehouseDate || !storageCondition) {
            alert("Vui lòng nhập đầy đủ thông tin: Ngày thu hoạch, Ngày nhập kho, Điều kiện bảo quản");
            return;
        }
        
        try {
            const response = await fetch("/api/distributor/calculate-shelf-life", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    harvest_date: harvestDate,
                    warehouse_date: warehouseDate,
                    storage_condition: storageCondition,
                    shelf_life_days: 30
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                document.getElementById("dist-shelf-life").value = result.recommended_use_by_date;
                document.getElementById("dist-shelf-life-message").textContent = result.message;
                document.getElementById("dist-shelf-life-result").style.display = "block";
            }
        } catch (error) {
            console.error("Shelf life calculation error:", error);
            alert("Lỗi tính toán hạn sử dụng");
        }
    });
    
    // Elements - Navigation (already defined in mobile menu section above)
    const tabContents = document.querySelectorAll(".tab-content");
    
    // Elements - Farmer
    const farmerForm = document.getElementById("farmer-form");
    const micBtn = document.getElementById("voice-mic-btn");
    const voiceStatus = document.getElementById("voice-status");
    const voiceRawText = document.getElementById("voice-raw-text");
    const scenarioChips = document.querySelectorAll(".scenario-chip");
    const aiDiagnostics = document.getElementById("ai-diagnostics");
    
    // Elements - Farmer QR Label preview
    const farmerQrLabel = document.getElementById("farmer-qr-label");
    const farmerLabelQrContainer = document.getElementById("farmer-label-qr-container");
    const farmerLabelLotId = document.getElementById("farmer-label-lot-id");
    const btnPrintSimulation = document.getElementById("btn-print-simulation");
    const btnScanAsConsumerNow = document.getElementById("btn-scan-as-consumer-now");
    
    // Elements - Transporter
    const transLotSelect = document.getElementById("trans-lot-select");
    const transporterForm = document.getElementById("transporter-form");
    const transNoLotMsg = document.getElementById("trans-no-lot-msg");
    const transTempSlider = document.getElementById("trans-temp");
    const transTempLabel = document.getElementById("trans-temp-label");
    
    // Elements - Transporter Simulator Scanner
    const btnTransScanCam  = document.getElementById("btn-trans-scan-cam");
    const btnTransScanFile = document.getElementById("btn-trans-scan-file");
    const transFileInput   = document.getElementById("trans-file-input");
    const transVideo       = document.getElementById("trans-video");
    const transViewfinder  = document.getElementById("trans-viewfinder");
    const transLaser       = document.getElementById("trans-laser");
    const transScannerPlaceholder = document.getElementById("trans-scanner-placeholder");
    const transScannerSuccess     = document.getElementById("trans-scanner-success");
    const transScannedLotDisplay  = document.getElementById("trans-scanned-lot-display");
    
    // Elements - Distributor
    const distLotSelect    = document.getElementById("dist-lot-select");
    const distributorForm  = document.getElementById("distributor-form");
    const distNoLotMsg     = document.getElementById("dist-no-lot-msg");
    
    // Elements - Distributor Simulator Scanner
    const btnDistScanCam  = document.getElementById("btn-dist-scan-cam");
    const btnDistScanFile = document.getElementById("btn-dist-scan-file");
    const distFileInput   = document.getElementById("dist-file-input");
    const distVideo       = document.getElementById("dist-video");
    const distViewfinder  = document.getElementById("dist-viewfinder");
    const distLaser       = document.getElementById("dist-laser");
    const distScannerPlaceholder = document.getElementById("dist-scanner-placeholder");
    const distScannerSuccess     = document.getElementById("dist-scanner-success");
    const distScannedLotDisplay  = document.getElementById("dist-scanned-lot-display");
    
    // Elements - Consumer
    const consumerSearchInput = document.getElementById("consumer-search-input");
    const consumerSearchBtn = document.getElementById("consumer-search-btn");
    const traceResultArea = document.getElementById("trace-result-area");
    const traceNoSearchMsg = document.getElementById("trace-no-search-msg");
    
    const traceDisplayLotId = document.getElementById("trace-display-lot-id");
    const verificationStatusBox = document.getElementById("verification-status-box");
    const verificationStatusEmpty = document.getElementById("verification-status-empty");
    const statusBadge = document.getElementById("status-badge");
    const qrCodeContainer = document.getElementById("qr-code-container");
    const qrUrlText = document.getElementById("qr-url-text");
    
    // Timeline fields
    const stepFarmer = document.getElementById("step-farmer");
    const badgeFarmer = document.getElementById("badge-farmer");
    const detVariety = document.getElementById("det-variety");
    const detPlantingDate = document.getElementById("det-planting-date");
    const detHarvestDate = document.getElementById("det-harvest-date");
    const detYield = document.getElementById("det-yield");
    const detFertilizer = document.getElementById("det-fertilizer");
    const detPesticide = document.getElementById("det-pesticide");
    const detQuality = document.getElementById("det-quality");
    const hashFarmer = document.getElementById("hash-farmer");
    
    const stepTransport = document.getElementById("step-transport");
    const badgeTransport = document.getElementById("badge-transport");
    const detTransportDetails = document.getElementById("det-transport-details");
    const detPickupDate = document.getElementById("det-pickup-date");
    const detTemp = document.getElementById("det-temp");
    const detCondition = document.getElementById("det-condition");
    const detDeliveryDate = document.getElementById("det-delivery-date");
    const detTransitTime = document.getElementById("det-transit-time");
    const hashTransport = document.getElementById("hash-transport");
    
    const stepDistributor = document.getElementById("step-distributor");
    const badgeDistributor = document.getElementById("badge-distributor");
    const detDistributorDetails = document.getElementById("det-distributor-details");
    const detWarehouseDate = document.getElementById("det-warehouse-date");
    const detStorageCondition = document.getElementById("det-storage-condition");
    const detRetailDate = document.getElementById("det-retail-date");
    const hashDistributor = document.getElementById("hash-distributor");
    
    // Elements - Hacker Lab
    const hackerLabCard = document.getElementById("hacker-lab");
    const hackerSelectField = document.getElementById("hacker-select-field");
    const hackerFakeValue = document.getElementById("hacker-fake-value");
    const hackerTamperBtn = document.getElementById("hacker-tamper-btn");
    
    // Elements - Explorer
    const explorerContainer = document.getElementById("blockchain-explorer-container");
    const blockchainIntegrityStatus = document.getElementById("blockchain-integrity-status");
    
    // Elements - Mining overlay loader
    const miningOverlay = document.getElementById("mining-overlay");
    const miningOverlayText = document.getElementById("mining-overlay-text");
    const miningOverlayHash = document.getElementById("mining-overlay-hash");
    
    // Set default dates
    const today = new Date().toISOString().split("T")[0];
    document.getElementById("farmer-planting-date").value = "2025-10-15";
    document.getElementById("farmer-harvest-date").value = today;
    
    // Initialize QR Code generator variable
    let qrcode = null;

    // ============= AUTO-SAVE DRAFT HANDLERS =============
    
    // Auto-save farmer form draft on input change
    const farmerFormFields = [
        "farmer-lot-id", "farmer-area-code", "farmer-variety", "farmer-planting-date", 
        "farmer-last-spray-date", "farmer-fertilizer", "farmer-pesticide", 
        "farmer-harvest-date", "farmer-yield", "farmer-brix", "farmer-quality"
    ];

    farmerFormFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener("change", () => {
                const draftData = {
                    lot_id: document.getElementById("farmer-lot-id").value,
                    planting_area_code: document.getElementById("farmer-area-code").value,
                    variety: document.getElementById("farmer-variety").value,
                    planting_date: document.getElementById("farmer-planting-date").value,
                    last_spray_date: document.getElementById("farmer-last-spray-date").value,
                    fertilizer: document.getElementById("farmer-fertilizer").value,
                    pesticide: document.getElementById("farmer-pesticide").value,
                    harvest_date: document.getElementById("farmer-harvest-date").value,
                    yield_kg: document.getElementById("farmer-yield").value || "0",
                    brix_value: document.getElementById("farmer-brix").value,
                    quality: document.getElementById("farmer-quality").value
                };
                farmerDraftManager.save(draftData);
            });
        }
    });

    // Load draft when farmer tab is activated
    const farmerTab = document.querySelector("[data-tab='farmer']");
    if (farmerTab) {
        const tabButton = Array.from(navButtons).find(btn => btn.getAttribute("data-tab") === "farmer");
        if (tabButton) {
            tabButton.addEventListener("click", () => {
                // Auto-load draft if available
                const draft = farmerDraftManager.load();
                if (draft) {
                    // Show recovery notification
                    const notification = document.createElement("div");
                    notification.className = "draft-recovery-notification";
                    notification.innerHTML = `
                        <i class="fa-solid fa-inbox"></i>
                        <span>Phát hiện nháp: <strong>${draft.lot_id || 'Chưa có mã lô'}</strong></span>
                        <button type="button" id="restore-draft-btn">Khôi phục</button>
                        <button type="button" id="discard-draft-btn">Bỏ qua</button>
                    `;
                    
                    const tabContent = document.getElementById("farmer");
                    if (tabContent) {
                        const existingNotif = tabContent.querySelector(".draft-recovery-notification");
                        if (existingNotif) existingNotif.remove();
                        tabContent.insertBefore(notification, tabContent.firstChild);
                        
                        document.getElementById("restore-draft-btn").addEventListener("click", () => {
                            document.getElementById("farmer-lot-id").value = draft.lot_id || "";
                            document.getElementById("farmer-area-code").value = draft.planting_area_code || "";
                            document.getElementById("farmer-variety").value = draft.variety || "Quýt Hồng Lai Vung";
                            document.getElementById("farmer-planting-date").value = draft.planting_date || "2025-10-15";
                            document.getElementById("farmer-last-spray-date").value = draft.last_spray_date || "";
                            document.getElementById("farmer-harvest-date").value = draft.harvest_date || today;
                            document.getElementById("farmer-fertilizer").value = draft.fertilizer || "";
                            document.getElementById("farmer-pesticide").value = draft.pesticide || "";
                            document.getElementById("farmer-yield").value = draft.yield_kg || "";
                            document.getElementById("farmer-brix").value = draft.brix_value || "";
                            document.getElementById("farmer-quality").value = draft.quality || "";
                            
                            // Trigger PHI calculation
                            if (typeof calculatePHI === "function") calculatePHI();
                            
                            notification.remove();
                        });
                        
                        document.getElementById("discard-draft-btn").addEventListener("click", () => {
                            farmerDraftManager.clear();
                            notification.remove();
                        });
                    }
                }
            });
        }
    }

    // Tương tự cho Transporter và Distributor
    // Auto-save transporter form draft on input change
    const transporterFormFields = [
        "trans-pickup-date", "trans-time", "trans-temp", 
        "trans-condition", "trans-delivery-date"
    ];

    transporterFormFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener("change", () => {
                if (transLotSelect.value) {
                    const draftData = {
                        lot_id: transLotSelect.value,
                        pickup_date: document.getElementById("trans-pickup-date").value,
                        transit_time: document.getElementById("trans-time").value,
                        temperature: document.getElementById("trans-temp").value,
                        condition: document.getElementById("trans-condition").value,
                        delivery_date: document.getElementById("trans-delivery-date").value
                    };
                    transporterDraftManager.save(draftData);
                }
            });
        }
    });

    // Auto-save distributor form draft on input change
    const distributorFormFields = [
        "dist-warehouse-date", "dist-storage", "dist-retail-date"
    ];

    distributorFormFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener("change", () => {
                if (distLotSelect.value) {
                    const draftData = {
                        lot_id: distLotSelect.value,
                        warehouse_date: document.getElementById("dist-warehouse-date").value,
                        storage_condition: document.getElementById("dist-storage").value,
                        retail_date: document.getElementById("dist-retail-date").value
                    };
                    distributorDraftManager.save(draftData);
                }
            });
        }
    });

    // ----------------- TAB NAVIGATION -----------------
    function switchTab(tabId) {
        navButtons.forEach(b => {
            if (b.getAttribute("data-tab") === tabId) {
                b.classList.add("active");
            } else {
                b.classList.remove("active");
            }
        });
        tabContents.forEach(c => {
            if (c.id === tabId) {
                c.classList.add("active");
            } else {
                c.classList.remove("active");
            }
        });
        
        // Trigger role-specific data loading
        if (tabId === "transporter") {
            loadLotsForTransporter();
        } else if (tabId === "distributor") {
            loadLotsForDistributor();
        } else if (tabId === "explorer") {
            loadBlockchainExplorer();
        }
    }

    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const tabId = btn.getAttribute("data-tab");
            switchTab(tabId);
        });
    });

    // ============= AUTO-DETECT QR HASH & LOAD CONSUMER TAB =============
    function handleQrHashNavigation() {
        // Detect URL hash format: /#consumer?id=QL-01
        const hash = window.location.hash;
        if (hash.includes("consumer") && hash.includes("id=")) {
            // Parse lot_id from hash
            const params = new URLSearchParams(hash.substring(hash.indexOf("?") + 1));
            const lotId = params.get("id");
            
            if (lotId) {
                console.log(`✓ Auto-detect QR hash: switching to consumer tab with lot_id=${lotId}`);
                // Switch to consumer tab
                switchTab("consumer");
                
                // Auto-fill search input and trigger search
                setTimeout(() => {
                    consumerSearchInput.value = lotId;
                    consumerSearchBtn.click();
                }, 300);
            }
        }
    }
    
    // Call on page load
    handleQrHashNavigation();
    
    // Also handle hash changes (for browser back/forward buttons)
    window.addEventListener("hashchange", handleQrHashNavigation);

    // ----------------- MINING OVERLAY LOADER -----------------
    function showMiningOverlay(message, onComplete) {
        miningOverlay.style.display = "flex";
        miningOverlayText.innerText = message;
        
        let progress = 0;
        const interval = setInterval(() => {
            progress += 1;
            const fakeNonce = Math.floor(Math.random() * 999999);
            const fakeHash = "00" + Array.from({length: 62}, () => Math.floor(Math.random()*16).toString(16)).join("");
            miningOverlayHash.innerHTML = `Nonce: <span style='color: var(--accent-gold)'>${fakeNonce}</span><br>Checking Hash: <span style='color: var(--text-secondary)'>${fakeHash}</span>`;
            
            if (progress >= 15) {
                clearInterval(interval);
                miningOverlay.style.display = "none";
                if (onComplete) onComplete();
            }
        }, 100);
    }

    // ----------------- SPEECH RECOGNITION / AI VOICE SIMULATION -----------------
    let recognition = null;
    let isRecordingActive = false;  // Track recording state
    let silenceTimeout = null;
    let maxRecordingDuration = null;
    const SILENCE_DURATION = 3000;  // Stop after 3 seconds of silence
    const MAX_RECORDING_TIME = 120000;  // Max 2 minutes
    
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRec();
        recognition.continuous = true;  // ✅ Keep recording even with pauses
        recognition.lang = 'vi-VN';
        recognition.interimResults = true;  // ✅ Show interim results in real-time
        recognition.maxAlternatives = 1;
        
        recognition.onstart = () => {
            isRecordingActive = true;
            micBtn.classList.add("recording");
            voiceStatus.innerText = "🎤 Đang ghi âm... Nói tiếp cho đến khi bạn hoàn thành (3 giây âm lặng = tự dừng)";
            voiceStatus.className = "voice-status recording";
            
            // Show audio level indicator
            const audioLevelDiv = document.getElementById("voice-audio-level");
            if (audioLevelDiv) audioLevelDiv.style.display = "block";
            
            // Change button to "Stop" during recording
            micBtn.innerHTML = '<i class="fa-solid fa-microphone-slash"></i> Dừng ghi âm';
            micBtn.style.background = "var(--error-red)";
            
            // Set max recording duration timeout
            maxRecordingDuration = setTimeout(() => {
                if (isRecordingActive && recognition) {
                    console.log("Max recording duration reached");
                    recognition.stop();
                    voiceStatus.innerText = "⏱️ Đạt giới hạn thời gian ghi âm tối đa (2 phút)";
                }
            }, MAX_RECORDING_TIME);
            
            // Play start sound
            playAudioFeedback('start');
        };
        
        recognition.onerror = (event) => {
            console.error("[Speech Recognition Error]", event.error);
            
            const errorMessages = {
                'network': '🌐 Lỗi kết nối mạng. Kiểm tra internet và thử lại...',
                'service_not_available': '🔌 Dịch vụ không khả dụng. Thử lại sau...',
                'no-speech': '🔇 Không phát hiện tiếng nói. Hãy nói rõ hơn...',
                'audio-capture': '🎤 Không thể truy cập microphone. Kiểm tra quyền...',
                'permission-denied': '🔒 Quyền microphone bị từ chối. Cho phép trong cài đặt trình duyệt...',
                'not-allowed': '❌ Ghi âm không được phép (HTTPS yêu cầu)'
            };
            
            const errorMsg = errorMessages[event.error] || `❌ Lỗi: ${event.error}`;
            voiceStatus.innerText = errorMsg;
            
            // Auto-retry for network errors
            if (event.error === 'network' || event.error === 'service_not_available') {
                setTimeout(() => {
                    if (isRecordingActive && recognition) {
                        try {
                            recognition.start();
                        } catch(e) {
                            console.error("Retry failed:", e);
                        }
                    }
                }, 1500);
            } else {
                recognition.stop();
                playAudioFeedback('error');
            }
        };
        
        recognition.onend = () => {
            isRecordingActive = false;
            micBtn.classList.remove("recording");
            voiceStatus.className = "voice-status";
            
            // Clear timeouts
            clearTimeout(silenceTimeout);
            clearTimeout(maxRecordingDuration);
            
            // Hide audio level indicator
            const audioLevelDiv = document.getElementById("voice-audio-level");
            if (audioLevelDiv) {
                audioLevelDiv.style.display = "none";
                const audioFill = document.getElementById("voice-audio-fill");
                if (audioFill) audioFill.style.width = "0%";
            }
            
            // Reset button to "Start"
            micBtn.innerHTML = '<i class="fa-solid fa-microphone"></i> Bắt đầu ghi âm';
            micBtn.style.background = "";
            
            // Process the recorded text when recording ends
            const finalText = voiceRawText.value.trim();
            if (finalText) {
                voiceStatus.innerText = "✅ Ghi âm hoàn thành! Đang xử lý...";
                playAudioFeedback('success');
                // Slight delay to ensure UI updates
                setTimeout(() => {
                    processVoiceText(finalText);
                }, 500);
            } else {
                voiceStatus.innerText = "⚠️ Không phát hiện âm thanh. Hãy thử lại.";
                playAudioFeedback('warning');
            }
        };
        
        let interimTranscript = "";  // Store interim results
        let lastResultTime = Date.now();
        
        recognition.onresult = (event) => {
            // Reset silence timeout on any result
            clearTimeout(silenceTimeout);
            lastResultTime = Date.now();
            
            interimTranscript = "";
            let finalTranscript = "";
            let confidence = 0;
            
            // Collect all results (interim + final)
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                const conf = event.results[i][0].confidence || 0;
                
                if (event.results[i].isFinal) {
                    finalTranscript += transcript + " ";
                    confidence = conf;  // Get confidence from final result
                } else {
                    interimTranscript += transcript;
                }
            }
            
            // Combine with previous results
            let fullText = voiceRawText.value;
            
            // Append final transcript
            if (finalTranscript) {
                fullText += finalTranscript;
                voiceRawText.value = fullText.trim();
                interimTranscript = "";  // Clear interim
                
                // Display confidence score
                const confidenceScore = document.getElementById("voice-confidence-score");
                if (confidenceScore && confidence > 0) {
                    const confPercent = Math.round(confidence * 100);
                    confidenceScore.innerText = `🎯 ${confPercent}% chắc chắn`;
                }
            }
            
            // Show current status
            let displayText = fullText + interimTranscript;
            if (interimTranscript) {
                voiceStatus.innerText = `🎤 Ghi âm: "${displayText}" (tạm thời)...`;
            } else if (finalTranscript) {
                voiceStatus.innerText = `🎤 Ghi âm: "${displayText}" ✓`;
            }
            
            // Set silence timeout - stop recording after 3 seconds of silence
            silenceTimeout = setTimeout(() => {
                if (isRecordingActive && recognition) {
                    console.log("Silence detected - stopping recording");
                    recognition.stop();
                }
            }, SILENCE_DURATION);
        };
    } else {
        voiceStatus.innerText = "⚠️ Trình duyệt không hỗ trợ Web Speech API. Dùng nút mô phỏng bên dưới.";
    }

    micBtn.addEventListener("click", () => {
        if (recognition) {
            if (isRecordingActive) {
                // Stop recording if it's active
                recognition.stop();
                isRecordingActive = false;
                clearTimeout(silenceTimeout);
                clearTimeout(maxRecordingDuration);
            } else {
                // Start recording
                voiceRawText.value = "";  // Clear previous text
                document.getElementById("voice-confidence-score").innerText = "";
                try {
                    recognition.start();
                } catch (e) {
                    console.error("Failed to start recognition:", e);
                    voiceStatus.innerText = "❌ Lỗi khởi động ghi âm";
                    playAudioFeedback('error');
                }
            }
        } else {
            // Simulator fallback if speech recognition is not supported
            const randomScenario = scenarioChips[Math.floor(Math.random() * scenarioChips.length)];
            const text = randomScenario.getAttribute("data-text");
            simulateSpeechInput(text);
        }
    });

    scenarioChips.forEach(chip => {
        chip.addEventListener("click", () => {
            const text = chip.getAttribute("data-text");
            simulateSpeechInput(text);
        });
    });

    function simulateSpeechInput(text) {
        voiceRawText.value = text;
        voiceStatus.innerText = "🎤 Mô phỏng: " + text.substring(0, 50) + "...";
        voiceStatus.className = "voice-status recording";
        playAudioFeedback('start');
        
        setTimeout(() => {
            voiceStatus.innerText = "✅ Xử lý AI thành công! Đang phân tích...";
            voiceStatus.className = "voice-status";
            playAudioFeedback('success');
            processVoiceText(text);
        }, 1500);
    }
    
    // Audio feedback function
    function playAudioFeedback(type) {
        // Create audio context for simple beep
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            switch(type) {
                case 'start':
                    oscillator.frequency.value = 800;
                    gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);
                    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
                    oscillator.start(audioContext.currentTime);
                    oscillator.stop(audioContext.currentTime + 0.1);
                    break;
                case 'success':
                    oscillator.frequency.value = 1000;
                    gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);
                    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.15);
                    oscillator.start(audioContext.currentTime);
                    oscillator.stop(audioContext.currentTime + 0.15);
                    break;
                case 'error':
                    oscillator.frequency.value = 300;
                    gainNode.gain.setValueAtTime(0.15, audioContext.currentTime);
                    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
                    oscillator.start(audioContext.currentTime);
                    oscillator.stop(audioContext.currentTime + 0.3);
                    break;
                case 'warning':
                    oscillator.frequency.value = 600;
                    gainNode.gain.setValueAtTime(0.15, audioContext.currentTime);
                    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
                    oscillator.start(audioContext.currentTime);
                    oscillator.stop(audioContext.currentTime + 0.2);
                    break;
            }
        } catch(e) {
            console.log("Audio feedback not available:", e);
        }
    }

    function processVoiceText(text) {
        aiDiagnostics.innerHTML = `[Info] Đang gửi text về Backend phân tích...\n[Text] "${text}"`;
        
        const feedbackContainer = document.getElementById("voice-ai-feedback-container");
        const completionBadge = document.getElementById("voice-completion-badge");
        const feedbackMsg = document.getElementById("voice-feedback-msg");
        const missingFieldsBox = document.getElementById("voice-missing-fields-box");
        const missingFieldsList = document.getElementById("voice-missing-fields-list");
        const feedbackIcon = document.getElementById("voice-feedback-icon");
        
        fetch("/api/ai/parse-voice", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const parsed = data.parsed_data;
                
                // Chuẩn hóa Lot ID và Area Code phía Client-side trước khi điền form
                let lotId = parsed.lot_id || "";
                if (lotId) {
                    lotId = lotId.toUpperCase().replace(/\s+/g, "");
                    if (!lotId.includes("-")) {
                        lotId = lotId.replace(/^([A-Z]+)(\d+)$/, "$1-$2");
                    }
                }
                
                let areaCode = parsed.planting_area_code || "";
                if (areaCode) {
                    areaCode = areaCode.toUpperCase()
                                       .replace(/[,.]/g, "")
                                       .replace(/\s+/g, "-")
                                       .replace(/-+/g, "-");
                }
                
                // Điền thông tin vào form
                document.getElementById("farmer-lot-id").value = lotId;
                if (areaCode) document.getElementById("farmer-area-code").value = areaCode;
                document.getElementById("farmer-variety").value = parsed.variety || "Quýt Hồng Lai Vung";
                if (parsed.planting_date) document.getElementById("farmer-planting-date").value = parsed.planting_date;
                if (parsed.harvest_date) document.getElementById("farmer-harvest-date").value = parsed.harvest_date;
                if (parsed.last_spray_date) {
                    document.getElementById("farmer-last-spray-date").value = parsed.last_spray_date;
                    if (typeof calculatePHI === "function") calculatePHI();
                }
                document.getElementById("farmer-fertilizer").value = parsed.fertilizer || "";
                document.getElementById("farmer-pesticide").value = parsed.pesticide || "";
                document.getElementById("farmer-yield").value = parsed.yield_kg || "";
                if (parsed.brix_value) document.getElementById("farmer-brix").value = parsed.brix_value;
                if (parsed.quality) document.getElementById("farmer-quality").value = parsed.quality;
                
                // ✓ LƯU NHÁP TỰ ĐỘNG SAU KHI ĐIỀN GIỌNG NÓI
                const draftData = {
                    lot_id: parsed.lot_id || "",
                    planting_area_code: parsed.planting_area_code || "",
                    variety: parsed.variety || "Quýt Hồng Lai Vung",
                    planting_date: parsed.planting_date || "",
                    last_spray_date: parsed.last_spray_date || "",
                    fertilizer: parsed.fertilizer || "",
                    pesticide: parsed.pesticide || "",
                    harvest_date: parsed.harvest_date || "",
                    yield_kg: parsed.yield_kg || "0",
                    brix_value: parsed.brix_value || "",
                    quality: parsed.quality || "",
                    is_complete: data.is_complete,
                    voice_raw_text: text
                };
                farmerDraftManager.save(draftData);
                
                // Thêm visual feedback cho draft
                const draftIndicator = document.getElementById("draft-status-farmer");
                if (draftIndicator) {
                    draftIndicator.style.display = "block";
                    draftIndicator.innerHTML = `<i class="fa-solid fa-floppy-disk"></i> Nháp đã lưu`;
                    setTimeout(() => {
                        draftIndicator.style.display = "none";
                    }, 3000);
                }
                
                // Hiển thị chuẩn đoán
                aiDiagnostics.innerHTML = `[SUCCESS] Bóc tách JSON thành công!\n[PROMPT TEMPLATE SENT TO LLM]:\n${data.prompt_used}\n\n[OUTPUT JSON PARSED]:\n${JSON.stringify(parsed, null, 2)}`;
                
                // Hiển thị và cập nhật AI Feedback Message Panel
                if (feedbackContainer) {
                    feedbackContainer.style.display = "block";
                    feedbackMsg.innerText = data.feedback_message || "Đã phân tích xong.";
                    
                    if (data.is_complete) {
                        completionBadge.innerText = "Hoàn thành";
                        completionBadge.className = "badge badge-verified";
                        feedbackIcon.style.color = "var(--success-green)";
                        feedbackIcon.style.background = "rgba(0, 230, 118, 0.1)";
                        missingFieldsBox.style.display = "none";
                        feedbackContainer.style.borderColor = "rgba(0, 230, 118, 0.3)";
                        feedbackContainer.style.background = "rgba(0, 230, 118, 0.02)";
                    } else {
                        completionBadge.innerText = "Thiếu thông tin";
                        completionBadge.className = "badge badge-warning";
                        feedbackIcon.style.color = "var(--accent-orange)";
                        feedbackIcon.style.background = "rgba(255, 122, 0, 0.1)";
                        feedbackContainer.style.borderColor = "rgba(255, 122, 0, 0.3)";
                        feedbackContainer.style.background = "rgba(255, 122, 0, 0.02)";
                        
                        if (data.missing_fields && data.missing_fields.length > 0) {
                            missingFieldsBox.style.display = "block";
                            missingFieldsList.innerText = data.missing_fields.join(", ");
                        } else {
                            missingFieldsBox.style.display = "none";
                        }
                    }
                }
            } else {
                aiDiagnostics.innerHTML = `[ERROR] Không thể xử lý dữ liệu: ${data.message}`;
                if (feedbackContainer) feedbackContainer.style.display = "none";
            }
        })
        .catch(err => {
            aiDiagnostics.innerHTML = `[ERROR] Lỗi kết nối API: ${err.message}`;
            if (feedbackContainer) feedbackContainer.style.display = "none";
        });
    }

    // ----------------- FARMER SUBMISSION -----------------
    farmerForm.addEventListener("submit", (e) => {
        e.preventDefault();
        
        const payload = {
            lot_id: document.getElementById("farmer-lot-id").value.trim().toUpperCase(),
            variety: document.getElementById("farmer-variety").value,
            planting_area_code: document.getElementById("farmer-area-code").value,
            planting_date: document.getElementById("farmer-planting-date").value,
            last_spray_date: document.getElementById("farmer-last-spray-date").value || null,
            fertilizer: document.getElementById("farmer-fertilizer").value,
            pesticide: document.getElementById("farmer-pesticide").value,
            harvest_date: document.getElementById("farmer-harvest-date").value,
            yield_kg: document.getElementById("farmer-yield").value || "0",
            quality: document.getElementById("farmer-quality").value,
            brix_value: document.getElementById("farmer-brix").value || null,
            post_harvest_washing: document.getElementById("farmer-washing").checked,
            post_harvest_sorting: document.getElementById("farmer-sorting").checked,
            post_harvest_packaging: document.getElementById("farmer-packaging").checked
        };
        
        showMiningOverlay("ĐANG TÍNH HASH & MỎ GIAO DỊCH NÔNG DÂN...", () => {
            fetch("/api/farmer/submit", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showSuccessModal({
                        title: "ĐĂNG KÝ THÀNH CÔNG!",
                        subtitle: `Lô hàng đã được đăng ký thành công vào chuỗi cung ứng của <strong>Quýt Hồng Lai Vung</strong> và đã đào khối.`,
                        lotId: payload.lot_id,
                        time: data.blockchain_transaction ? data.blockchain_transaction.timestamp : null,
                        status: "Đã xác thực trên Blockchain",
                        onViewDetails: () => {
                            const consumerTabBtn = document.querySelector('[data-tab="consumer"]');
                            if (consumerTabBtn) consumerTabBtn.click();
                            const searchInput = document.getElementById("consumer-search-input");
                            if (searchInput) searchInput.value = payload.lot_id;
                            performTrace(payload.lot_id);
                        }
                    });
                    
                    // Show QR Code Label
                    activeLotId = payload.lot_id;
                    farmerLabelLotId.innerText = `Mã lô: ${payload.lot_id}`;
                    // Sử dụng domain động hiện tại + backend endpoint /product/{lot_id} để hiển thị trực tiếp cho Zalo/Camera
                    const currentOrigin = window.location.origin;
                    const qrUrl = `${currentOrigin}/product/${payload.lot_id}`;
                    generateQrWithLogo(farmerLabelQrContainer, qrUrl, 128, "/static/logo.webp");
                    farmerQrLabel.style.display = "block";
                    
                    farmerForm.reset();
                    // Reset dates to default
                    document.getElementById("farmer-planting-date").value = "2025-10-15";
                    document.getElementById("farmer-harvest-date").value = today;
                    document.getElementById("farmer-variety").value = "Quýt Hồng Lai Vung";
                    
                    // ✓ XÓA NHÁP SAU KHI GỬI THÀNH CÔNG
                    farmerDraftManager.clear();
                    
                    // Show success notification
                    const notification = document.createElement("div");
                    notification.className = "submission-success-notification";
                    notification.innerHTML = `<i class="fa-solid fa-check-circle"></i> Nháp đã xóa, sẵn sàng nhập lô tiếp theo`;
                    farmerForm.parentElement.insertBefore(notification, farmerForm);
                    setTimeout(() => notification.remove(), 3000);
                } else {
                    parseAndShowAPIError("CẬP NHẬT THẤT BẠI!", data);
                }
            })
            .catch(err => showFailureModal("LỖI KẾT NỐI API!", "Không thể kết nối đến máy chủ.", err.message));
        });
    });

    // ----------------- TRANSPORTER LOGIC -----------------
    transTempSlider.addEventListener("input", (e) => {
        const val = parseFloat(e.target.value);
        transTempLabel.innerText = `Nhiệt độ bảo quản cảm biến xe lạnh: ${val} °C`;
        
        // Thay đổi màu label tùy nhiệt độ
        if (val < 2) {
            transTempLabel.style.color = "#00d2ff"; // Lạnh sâu
        } else if (val >= 2 && val <= 8) {
            transTempLabel.style.color = "var(--success-green)"; // Lý tưởng
        } else if (val > 8 && val <= 18) {
            transTempLabel.style.color = "var(--accent-gold)"; // Hơi ấm
        } else {
            transTempLabel.style.color = "var(--error-red)"; // Quá nóng
        }
    });

    function loadLotsForTransporter() {
        fetch("/api/lots")
        .then(res => res.json())
        .then(lots => {
            availableLots = lots;
            transLotSelect.innerHTML = '<option value="">-- Chọn lô quýt --</option>';
            
            // Chỉ hiển thị các lô đang ở giai đoạn FARMER (chưa vận chuyển)
            lots.forEach(lot => {
                if (lot.current_stage === "FARMER") {
                    transLotSelect.innerHTML += `<option value="${lot.lot_id}">${lot.lot_id} (${lot.variety})</option>`;
                }
            });
        });
    }

    transLotSelect.addEventListener("change", (e) => {
        const lotId = e.target.value;
        if (lotId) {
            transporterForm.style.display = "block";
            transNoLotMsg.style.display = "none";
            
            // Set default date values
            const now = new Date();
            const offset = now.getTimezoneOffset() * 60000;
            const localISOTime = new Date(now - offset).toISOString().slice(0, 16);
            document.getElementById("trans-pickup-date").value = localISOTime;
            
            // Giao hàng dự kiến sau 4 tiếng
            const deliveryTime = new Date(now.getTime() + 4 * 60 * 60 * 1000 - offset).toISOString().slice(0, 16);
            document.getElementById("trans-delivery-date").value = deliveryTime;
        } else {
            transporterForm.style.display = "none";
            transNoLotMsg.style.display = "block";
        }
    });

    transporterForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const lotId = transLotSelect.value;
        
        const payload = {
            lot_id: lotId,
            transporter_name: document.getElementById("trans-name").value,
            vehicle_plate: document.getElementById("trans-plate").value,
            driver_code: document.getElementById("trans-driver").value,
            pickup_date: document.getElementById("trans-pickup-date").value.replace("T", " "),
            pickup_time: document.getElementById("trans-pickup-time").value || null,
            eta: document.getElementById("trans-eta").value || null,
            transit_time: document.getElementById("trans-time").value,
            temperature: parseFloat(transTempSlider.value),
            humidity: document.getElementById("trans-humidity").value ? parseFloat(document.getElementById("trans-humidity").value) : null,
            condition: document.getElementById("trans-condition").value,
            delivery_date: document.getElementById("trans-delivery-date").value.replace("T", " "),
            weight_at_pickup: document.getElementById("trans-weight-pickup").value ? parseFloat(document.getElementById("trans-weight-pickup").value) : null,
            weight_at_delivery: document.getElementById("trans-weight-delivery").value ? parseFloat(document.getElementById("trans-weight-delivery").value) : null
        };
        
        showMiningOverlay("ĐANG ĐÀO KHỐI BLOCK CHỨA THÔNG TIN VẬN CHUYỂN...", () => {
            fetch("/api/transporter/update", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showSuccessModal({
                        title: "CẬP NHẬT THÀNH CÔNG!",
                        subtitle: `Thông tin vận chuyển đã được ghi nhận và lưu lên <strong>Blockchain</strong> của <strong>Quýt Hồng Lai Vung</strong>.`,
                        lotId: lotId,
                        time: null,
                        status: "Đã xác thực trên Blockchain",
                        onViewDetails: () => {
                            const consumerTabBtn = document.querySelector('[data-tab="consumer"]');
                            if (consumerTabBtn) consumerTabBtn.click();
                            const searchInput = document.getElementById("consumer-search-input");
                            if (searchInput) searchInput.value = lotId;
                            performTrace(lotId);
                        }
                    });
                    transporterForm.style.display = "none";
                    transLotSelect.value = "";
                    
                    // Reset scanner UI
                    transViewfinder.classList.remove("success-scan");
                    transScannerPlaceholder.style.display = "block";
                    transScannerSuccess.style.display = "none";
                    
                    // ✓ XÓA NHÁP SAU KHI GỬI THÀNH CÔNG
                    transporterDraftManager.clear();
                    
                    loadLotsForTransporter();
                } else {
                    parseAndShowAPIError("CẬP NHẬT THẤT BẠI!", data);
                }
            })
            .catch(err => showFailureModal("LỖI KẾT NỐI API!", "Không thể kết nối đến máy chủ.", err.message));
        });
    });

    // ----------------- DISTRIBUTOR LOGIC -----------------
    function loadLotsForDistributor() {
        fetch("/api/lots")
        .then(res => res.json())
        .then(lots => {
            availableLots = lots;
            distLotSelect.innerHTML = '<option value="">-- Chọn lô quýt --</option>';
            
            // Chỉ hiển thị các lô đang ở giai đoạn TRANSPORT (đã vận chuyển, chưa phân phối)
            lots.forEach(lot => {
                if (lot.current_stage === "TRANSPORT") {
                    distLotSelect.innerHTML += `<option value="${lot.lot_id}">${lot.lot_id} (${lot.variety})</option>`;
                }
            });
        });
    }

    distLotSelect.addEventListener("change", (e) => {
        const lotId = e.target.value;
        if (lotId) {
            distributorForm.style.display = "block";
            distNoLotMsg.style.display = "none";
            document.getElementById("dist-warehouse-date").value = today;
            document.getElementById("dist-retail-date").value = today;
        } else {
            distributorForm.style.display = "none";
            distNoLotMsg.style.display = "block";
        }
    });

    distributorForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const lotId = distLotSelect.value;
        
        const payload = {
            lot_id: lotId,
            warehouse_date: document.getElementById("dist-warehouse-date").value,
            shelf_date: document.getElementById("dist-shelf-date").value || null,
            storage_condition: document.getElementById("dist-storage").value,
            display_condition: document.getElementById("dist-display").value || null,
            shelf_life_expiry: document.getElementById("dist-shelf-life").value || null,
            retail_date: document.getElementById("dist-retail-date").value
        };
        
        showMiningOverlay("ĐANG KHÓA HASH THÔNG TIN PHÂN PHỐI LÊN BLOCKCHAIN...", () => {
            fetch("/api/distributor/update", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showSuccessModal({
                        title: "HOÀN THÀNH XÁC NHẬN!",
                        subtitle: `Đã hoàn thành xác nhận chuỗi cung ứng cho lô hàng và đóng dấu lên <strong>Blockchain</strong> của <strong>Quýt Hồng Lai Vung</strong>.`,
                        lotId: lotId,
                        time: null,
                        status: "Đã xác thực trên Blockchain",
                        onViewDetails: () => {
                            const consumerTabBtn = document.querySelector('[data-tab="consumer"]');
                            if (consumerTabBtn) consumerTabBtn.click();
                            const searchInput = document.getElementById("consumer-search-input");
                            if (searchInput) searchInput.value = lotId;
                            performTrace(lotId);
                        }
                    });
                    distributorForm.style.display = "none";
                    distLotSelect.value = "";
                    
                    // Reset scanner UI
                    distViewfinder.classList.remove("success-scan");
                    distScannerPlaceholder.style.display = "block";
                    distScannerSuccess.style.display = "none";
                    
                    // ✓ XÓA NHÁP SAU KHI GỬI THÀNH CÔNG
                    distributorDraftManager.clear();
                    
                    loadLotsForDistributor();
                } else {
                    parseAndShowAPIError("CẬP NHẬT THẤT BẠI!", data);
                }
            })
            .catch(err => showFailureModal("LỖI KẾT NỐI API!", "Không thể kết nối đến máy chủ.", err.message));
        });
    });

    // ----------------- CONSUMER PORTAL (QR SEARCH) -----------------
    consumerSearchBtn.addEventListener("click", () => {
        const lotId = consumerSearchInput.value.trim().toUpperCase();
        if (!lotId) {
            showFailureModal("CẢNH BÁO TRUY VẾT!", "Vui lòng nhập mã lô hàng.", "Mã lô hàng không thể bỏ trống khi thực hiện tra cứu.");
            return;
        }
        performTrace(lotId);
    });

    function performTrace(lotId) {
        fetch(`/api/trace/${lotId}`)
        .then(res => {
            if (!res.ok) {
                throw new Error("Không tồn tại mã lô quýt này trên hệ thống.");
            }
            return res.json();
        })
        .then(data => {
            activeLotId = lotId;
            traceDisplayLotId.innerText = lotId;
            traceResultArea.style.display = "block";
            traceNoSearchMsg.style.display = "none";
            
            // Cập nhật ngữ cảnh cho Chatbot AI
            if (window.updateChatbotLotContext) {
                window.updateChatbotLotContext(data);
            }

            
            // 1. Farmer Data
            const farmer = data.data.farmer;
            const farmerVerify = data.blockchain_verification.farmer;
            
            detVariety.innerText = farmer.variety;
            detPlantingDate.innerText = formatDate(farmer.planting_date);
            detHarvestDate.innerText = formatDate(farmer.harvest_date);
            detYield.innerText = farmer.yield_kg + " kg";
            detFertilizer.innerText = farmer.fertilizer;
            detPesticide.innerText = farmer.pesticide;
            detQuality.innerText = farmer.quality;
            
            hashFarmer.innerHTML = `<div>Hash thực tế SQLite: <span style="color: var(--accent-gold)">${farmerVerify.computed_hash}</span></div>
                                   <div>Hash khóa Blockchain: <span style="color: ${farmerVerify.verified ? 'var(--success-green)' : 'var(--error-red)'}">${farmerVerify.blockchain_hash}</span></div>`;
            
            if (farmerVerify.verified) {
                badgeFarmer.innerText = "Xác Thực Sổ Cái";
                badgeFarmer.className = "badge badge-verified";
                stepFarmer.className = "timeline-step completed";
            } else {
                badgeFarmer.innerText = "HASH BỊ LỆCH (GIẢ MẠO!)";
                badgeFarmer.className = "badge badge-warning";
                stepFarmer.className = "timeline-step active";
            }

            // 2. Transport Data
            const transporter = data.data.transporter;
            if (transporter) {
                const transVerify = data.blockchain_verification.transporter;
                detTransportDetails.style.display = "grid";
                hashTransport.style.display = "block";
                
                detPickupDate.innerText = transporter.pickup_date;
                detTemp.innerText = transporter.temperature + " °C";
                detCondition.innerText = transporter.condition;
                detDeliveryDate.innerText = transporter.delivery_date;
                detTransitTime.innerText = transporter.transit_time;
                
                // Colorize temperature indicator
                if (transporter.temperature <= 8 && transporter.temperature >= 2) {
                    detTemp.innerHTML += ` <span style="color: var(--success-green); font-size: 0.8rem;">(Tối ưu)</span>`;
                } else {
                    detTemp.innerHTML += ` <span style="color: var(--error-red); font-size: 0.8rem;">(Cảnh báo bảo quản)</span>`;
                }

                hashTransport.innerHTML = `<div>Hash thực tế SQLite: <span style="color: var(--accent-gold)">${transVerify.computed_hash}</span></div>
                                           <div>Hash khóa Blockchain: <span style="color: ${transVerify.verified ? 'var(--success-green)' : 'var(--error-red)'}">${transVerify.blockchain_hash}</span></div>`;
                
                if (transVerify.verified) {
                    badgeTransport.innerText = "Xác Thực Sổ Cái";
                    badgeTransport.className = "badge badge-verified";
                    stepTransport.className = "timeline-step completed";
                } else {
                    badgeTransport.innerText = "HASH BỊ LỆCH (GIẢ MẠO!)";
                    badgeTransport.className = "badge badge-warning";
                    stepTransport.className = "timeline-step active";
                }
            } else {
                detTransportDetails.style.display = "none";
                hashTransport.style.display = "none";
                badgeTransport.innerText = "Chờ Tiếp Nhận";
                badgeTransport.className = "badge badge-pending";
                stepTransport.className = "timeline-step";
            }

            // 3. Distributor Data
            const distributor = data.data.distributor;
            if (distributor) {
                const distVerify = data.blockchain_verification.distributor;
                detDistributorDetails.style.display = "grid";
                hashDistributor.style.display = "block";
                
                detWarehouseDate.innerText = formatDate(distributor.warehouse_date);
                detStorageCondition.innerText = distributor.storage_condition;
                detRetailDate.innerText = formatDate(distributor.retail_date);
                
                hashDistributor.innerHTML = `<div>Hash thực tế SQLite: <span style="color: var(--accent-gold)">${distVerify.computed_hash}</span></div>
                                             <div>Hash khóa Blockchain: <span style="color: ${distVerify.verified ? 'var(--success-green)' : 'var(--error-red)'}">${distVerify.blockchain_hash}</span></div>`;
                
                if (distVerify.verified) {
                    badgeDistributor.innerText = "Xác Thực Sổ Cái";
                    badgeDistributor.className = "badge badge-verified";
                    stepDistributor.className = "timeline-step completed";
                } else {
                    badgeDistributor.innerText = "HASH BỊ LỆCH (GIẢ MẠO!)";
                    badgeDistributor.className = "badge badge-warning";
                    stepDistributor.className = "timeline-step active";
                }
            } else {
                detDistributorDetails.style.display = "none";
                hashDistributor.style.display = "none";
                badgeDistributor.innerText = "Chờ Phân Phối";
                badgeDistributor.className = "badge badge-pending";
                stepDistributor.className = "timeline-step";
            }

            // 4. Overarching Security Badge (Tampered check)
            verificationStatusBox.style.display = "block";
            verificationStatusEmpty.style.display = "none";
            hackerLabCard.style.display = "block"; // Show hacker options for active lot
            
            if (data.blockchain_verification.is_tampered) {
                statusBadge.innerText = "CẢNH BÁO: Dữ liệu Bị Sửa Đổi!";
                statusBadge.className = "status-badge-large tampered";
                statusBadge.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> CẢNH BÁO: DỮ LIỆU ĐÃ BỊ THAY ĐỔI TRÁI PHÉP!`;
            } else {
                statusBadge.innerText = "Xác Thực An Toàn";
                statusBadge.className = "status-badge-large verified";
                statusBadge.innerHTML = `<i class="fa-solid fa-shield-halved"></i> XÁC THỰC AN TOÀN TRÊN SỔ CÁI`;
            }

            // 5. Generate Dynamic QR Code
            generateQrCode(lotId);
        })
        .catch(err => {
            showFailureModal("TRUY VẾT THẤT BẠI!", "Không tìm thấy thông tin truy vết lô hàng.", err.message);
            traceResultArea.style.display = "none";
            traceNoSearchMsg.style.display = "block";
            verificationStatusBox.style.display = "none";
            verificationStatusEmpty.style.display = "block";
            hackerLabCard.style.display = "none";
            
            // Xóa ngữ cảnh Chatbot AI
            if (window.clearChatbotLotContext) {
                window.clearChatbotLotContext();
            }
        });
    }

    function generateQrCode(lotId) {
        // Sử dụng tên miền hiện tại của trình duyệt (localhost hoặc Render) để liên kết QR động
        const currentOrigin = window.location.origin;
        const qrUrl = `${currentOrigin}/product/${lotId}`;
        qrUrlText.innerText = `Liên kết QR: ${qrUrl}`;
        generateQrWithLogo(qrCodeContainer, qrUrl, 128, "/static/logo.webp");
    }

    // ----------------- HACKER SECURITY LAB SIMULATOR -----------------
    hackerTamperBtn.addEventListener("click", () => {
        if (!activeLotId) return;
        
        const field = hackerSelectField.value;
        const fakeValue = hackerFakeValue.value.trim();
        
        if (!fakeValue) {
            alert("Vui lòng điền giá trị giả mạo.");
            return;
        }

        if (confirm(`Bạn có chắc chắn muốn TẤN CÔNG trực tiếp vào CSDL SQLite để sửa đổi trường dữ liệu '${field}' thành '${fakeValue}' của lô ${activeLotId} không?\n\n(Hệ thống Blockchain sẽ KHÔNG thay đổi giao dịch cũ để xem nó phát hiện giả mạo như thế nào)`)) {
            fetch("/api/tamper", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    lot_id: activeLotId,
                    field: field,
                    value: fakeValue
                })
            })
            .then(res => res.json())
            .then(data => {
                alert(data.message + "\nHãy bấm OK, trang sẽ tự động tải lại kết quả truy vết để đối chiếu Blockchain.");
                performTrace(activeLotId);
            })
            .catch(err => alert("Lỗi tấn công: " + err.message));
        }
    });

    // ----------------- BLOCKCHAIN EXPLORER -----------------
    function loadBlockchainExplorer() {
        fetch("/api/blockchain/blocks")
        .then(res => res.json())
        .then(blocks => {
            explorerContainer.innerHTML = "";
            
            // Kiểm tra tính toàn vẹn của chuỗi (gọi check cục bộ)
            let isChainValid = true;
            for (let i = 1; i < blocks.length; i++) {
                if (blocks[i].previous_hash !== blocks[i-1].hash) {
                    isChainValid = false;
                }
            }
            
            if (isChainValid) {
                blockchainIntegrityStatus.className = "badge badge-verified";
                blockchainIntegrityStatus.innerHTML = '<i class="fa-solid fa-circle-check"></i> Chuỗi Toàn Vẹn (Integrity OK)';
            } else {
                blockchainIntegrityStatus.className = "badge badge-warning";
                blockchainIntegrityStatus.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Chuỗi Bị Phá Hủy (Broken Link!)';
            }

            // Loop and draw block cards in reverse order (newest blocks on top)
            const reversedBlocks = [...blocks].reverse();
            reversedBlocks.forEach(block => {
                const blockTime = new Date(block.timestamp * 1000).toLocaleString();
                
                let txHtml = "";
                block.transactions.forEach(tx => {
                    if (tx.info) {
                        // Genesis Block info
                        txHtml += `<div class="tx-item">
                                    <div style="font-weight: 600; color: var(--accent-orange);">${tx.info}</div>
                                   </div>`;
                    } else {
                        // Regular traceability hash registration
                        txHtml += `<div class="tx-item">
                                    <div class="tx-field-row">
                                        <strong style="color: var(--accent-gold);">${tx.lot_id}</strong>
                                        <span class="badge" style="background: rgba(255,255,255,0.05); font-size: 0.7rem;">${tx.stage}</span>
                                    </div>
                                    <div class="tx-field-row">
                                        <span style="font-size: 0.75rem; color: var(--text-secondary);">Ghi nhận lúc:</span>
                                        <span style="font-size: 0.75rem; color: var(--text-muted);">${tx.timestamp}</span>
                                    </div>
                                    <div class="tx-title" style="margin-top: 5px;">Mã băm dữ liệu nông sản (Data Hash):</div>
                                    <div class="tx-hash-val">${tx.data_hash}</div>
                                   </div>`;
                    }
                });

                explorerContainer.innerHTML += `
                    <div class="block-card">
                        <div class="block-header">
                            <span class="block-index"><i class="fa-solid fa-cube"></i> BLOCK #${block.index}</span>
                            <span class="block-time"><i class="fa-solid fa-clock"></i> Khai thác lúc: ${blockTime}</span>
                        </div>
                        <div class="block-hashes">
                            <div class="hash-row">
                                <span class="hash-label">Mã băm khối:</span>
                                <span class="hash-value" style="color: var(--accent-orange); font-weight: bold;">${block.hash}</span>
                            </div>
                            <div class="hash-row">
                                <span class="hash-label">Băm khối trước:</span>
                                <span class="hash-value">${block.previous_hash}</span>
                            </div>
                            <div class="hash-row">
                                <span class="hash-label">Nonce (Số ngẫu):</span>
                                <span class="hash-value" style="color: var(--accent-gold);">${block.nonce}</span>
                            </div>
                        </div>
                        <div class="block-txs">
                            <div class="tx-title"><i class="fa-solid fa-receipt"></i> Giao dịch chứa trong Block (${block.transactions.length})</div>
                            ${txHtml}
                        </div>
                    </div>
                `;
            });
        });
    }

    // ═══════════════════════════════════════════════════════
    // QR SCANNER ENGINE  (camera stream  +  file upload)
    // Uses jsQR library loaded in <head>
    // ═══════════════════════════════════════════════════════

    // Active camera stream handles (so we can stop them)
    let transStream = null;
    let distStream  = null;
    let transRafId  = null;   // requestAnimationFrame id
    let distRafId   = null;

    // ── Audio beep ──────────────────────────────────────────
    function playBeepSound() {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain); gain.connect(ctx.destination);
            osc.type = 'sine'; osc.frequency.value = 1400;
            gain.gain.setValueAtTime(0.08, ctx.currentTime);
            osc.start(); osc.stop(ctx.currentTime + 0.12);
        } catch(e) { /* browser blocked */ }
    }

    // ── Extract lot-id from a QR URL or raw text ─────────────
    // Supports URLs like https://lai-vung-network.onrender.com/#consumer?id=QL-01
    // or a bare lot ID like  QL-01
    function extractLotIdFromQr(text) {
        text = (text || "").trim();
        // Match hash-based URL: https://.../#consumer?id=LOT-01
        const mHash = text.match(/[#?]consumer[?&]id=([^&\s]+)/i);
        if (mHash) return mHash[1].toUpperCase();
        // Match path-based URL: https://.../product/LOT-01 (legacy)
        const mPath = text.match(/\/product\/([^/?#\s]+)/i);
        if (mPath) return mPath[1].toUpperCase();
        // Match ?id=LOT-01 or &id=LOT-01 directly
        const mId = text.match(/[?&]id=([^&\s]+)/i);
        if (mId) return mId[1].toUpperCase();
        // fallback: treat raw text as lot id if it looks like one (≤30 chars, no spaces)
        if (text && text.length <= 30 && !/\s/.test(text)) return text.toUpperCase();
        return null;
    }

    // ── Decode a single ImageData with jsQR ──────────────────
    function decodeImageData(imageData) {
        if (typeof jsQR === 'undefined') return null;
        const result = jsQR(imageData.data, imageData.width, imageData.height,
                            { inversionAttempts: "dontInvert" });
        return result ? result.data : null;
    }

    // ── Generic: stop a camera stream and clean up ────────────
    function stopStream(stream, rafId, video, stopBtn) {
        if (rafId) cancelAnimationFrame(rafId);
        if (stream) stream.getTracks().forEach(t => t.stop());
        video.srcObject = null;
        video.style.display = "none";
        if (stopBtn && stopBtn.parentNode) stopBtn.parentNode.removeChild(stopBtn);
        return [null, null];
    }

    // ── Generic camera-scan flow ──────────────────────────────
    // onFound(lotId) is called when a valid lot is decoded
    async function startCameraScan(cfg) {
        const { video, laser, placeholder, successEl, displayEl,
                lotSelect, viewfinder, scanCamBtn, onFound } = cfg;

        // If already scanning → stop
        if (video.srcObject) {
            if (cfg.stopStream) cfg.stopStream();
            return;
        }

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            alert("Trình duyệt không hỗ trợ camera. Hãy dùng chức năng tải ảnh QR thay thế.");
            return;
        }

        let stream;
        try {
            stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: "environment", width: { ideal: 640 }, height: { ideal: 480 } }
            });
        } catch(err) {
            alert(`Không thể truy cập camera: ${err.message}\n\nHãy dùng nút 'Tải ảnh QR để quét' thay thế.`);
            return;
        }

        cfg.currentStream = stream;

        // Show video feed inside viewfinder
        video.srcObject = stream;
        video.style.display = "block";
        placeholder.style.display = "none";
        successEl.style.display = "none";
        viewfinder.classList.remove("success-scan");
        viewfinder.classList.add("active");
        laser.style.display = "block";

        // Inject a Stop button
        const stopBtn = document.createElement("button");
        stopBtn.type = "button";
        stopBtn.className = "btn btn-secondary";
        stopBtn.style.cssText = "width:auto;padding:8px 16px;margin-top:8px;" +
                               "background:rgba(255,23,68,0.1);border:1px solid var(--error-red);color:var(--error-red);";
        stopBtn.innerHTML = '<i class="fa-solid fa-stop"></i> Dừng Camera';
        stopBtn.onclick = () => {
            [cfg.currentStream, cfg.currentRafId] = stopStream(
                cfg.currentStream, cfg.currentRafId, video, stopBtn);
            viewfinder.classList.remove("active");
            laser.style.display = "none";
            placeholder.style.display = "flex";
        };
        scanCamBtn.parentNode.insertBefore(stopBtn, scanCamBtn.nextSibling);
        cfg.stopBtn = stopBtn;

        // Off-screen canvas to grab frames
        const canvas = document.createElement("canvas");
        const ctx2d  = canvas.getContext("2d");

        function tick() {
            if (!video.srcObject) return;
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                canvas.width  = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx2d.drawImage(video, 0, 0, canvas.width, canvas.height);
                const imgData = ctx2d.getImageData(0, 0, canvas.width, canvas.height);
                const raw = decodeImageData(imgData);
                if (raw) {
                    const lotId = extractLotIdFromQr(raw);
                    if (lotId) {
                        // Stop camera
                        [cfg.currentStream, cfg.currentRafId] = stopStream(
                            cfg.currentStream, cfg.currentRafId, video, stopBtn);
                        cfg.stopBtn = null;
                        // Show success UI
                        viewfinder.classList.remove("active");
                        viewfinder.classList.add("success-scan");
                        laser.style.display = "none";
                        displayEl.innerText = `Đã nhận diện lô: ${lotId}`;
                        successEl.style.display = "block";
                        placeholder.style.display = "none";
                        playBeepSound();
                        onFound(lotId);
                        return;
                    }
                }
            }
            cfg.currentRafId = requestAnimationFrame(tick);
        }
        await video.play();
        cfg.currentRafId = requestAnimationFrame(tick);
    }

    // ── Generic file-upload QR decode ────────────────────────
    function startFileScan(cfg) {
        const { fileInput, placeholder, successEl, displayEl,
                laser, viewfinder, onFound } = cfg;
        fileInput.value = "";
        fileInput.click();
        fileInput.onchange = () => {
            const file = fileInput.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (ev) => {
                const img = new Image();
                img.onload = () => {
                    const canvas = document.createElement("canvas");
                    canvas.width  = img.width;
                    canvas.height = img.height;
                    const ctx2d = canvas.getContext("2d");
                    ctx2d.drawImage(img, 0, 0);
                    const imgData = ctx2d.getImageData(0, 0, canvas.width, canvas.height);
                    const raw = decodeImageData(imgData);
                    if (!raw) {
                        // Show the image in viewfinder anyway so user sees it
                        viewfinder.style.backgroundImage = `url('${ev.target.result}')`;
                        viewfinder.style.backgroundSize  = "cover";
                        alert("Không tìm thấy mã QR trong ảnh này.\nHãy chụp/tải ảnh rõ hơn và thử lại.");
                        return;
                    }
                    const lotId = extractLotIdFromQr(raw);
                    if (!lotId) {
                        alert(`Mã QR đọc được: "${raw}"\nNhưng không xác định được mã lô hàng hợp lệ.`);
                        return;
                    }
                    // Success
                    viewfinder.style.backgroundImage = "";
                    viewfinder.classList.remove("active");
                    viewfinder.classList.add("success-scan");
                    laser.style.display = "none";
                    placeholder.style.display = "none";
                    displayEl.innerText = `Đã nhận diện lô: ${lotId}`;
                    successEl.style.display = "block";
                    playBeepSound();
                    onFound(lotId);
                };
                img.src = ev.target.result;
            };
            reader.readAsDataURL(file);
        };
    }

    // ── Shared callback: lot identified → fill form ──────────
    async function onTransLotFound(lotId) {
        try {
            const res = await fetch("/api/lots");
            availableLots = await res.json();
            const lot = availableLots.find(l => l.lot_id === lotId);
            if (lot) {
                if (lot.current_stage !== "FARMER") {
                    showFailureModal("CẬP NHẬT THẤT BẠI!", `Lô hàng <strong>${lotId}</strong> đã được vận chuyển hoặc hoàn thành phân phối.`, "Không thể chỉnh sửa hoặc cập nhật lại thông tin ở giai đoạn này.");
                    transViewfinder.classList.remove("success-scan");
                    transScannerPlaceholder.style.display = "block";
                    transScannerSuccess.style.display = "none";
                    return;
                }
                transLotSelect.value = lotId;
                transLotSelect.dispatchEvent(new Event("change"));
            } else {
                showFailureModal("CẬP NHẬT THẤT BẠI!", `Lô hàng <strong>${lotId}</strong> không tồn tại trên hệ thống.`, "Vui lòng kiểm tra lại mã lô hàng hoặc đăng ký mới.");
                transViewfinder.classList.remove("success-scan");
                transScannerPlaceholder.style.display = "block";
                transScannerSuccess.style.display = "none";
            }
        } catch (err) {
            showFailureModal("LỖI HỆ THỐNG!", "Lỗi tải thông tin lô hàng từ máy chủ.", err.message);
        }
    }
    async function onDistLotFound(lotId) {
        try {
            const res = await fetch("/api/lots");
            availableLots = await res.json();
            const lot = availableLots.find(l => l.lot_id === lotId);
            if (lot) {
                if (lot.current_stage === "FARMER") {
                    showFailureModal("CẬP NHẬT THẤT BẠI!", `Lô hàng <strong>${lotId}</strong> chưa qua giai đoạn vận chuyển.`, "Vui lòng cập nhật thông tin vận chuyển trước khi thực hiện phân phối lẻ.");
                    distViewfinder.classList.remove("success-scan");
                    distScannerPlaceholder.style.display = "block";
                    distScannerSuccess.style.display = "none";
                    return;
                } else if (lot.current_stage === "DISTRIBUTOR") {
                    showFailureModal("CẬP NHẬT THẤT BẠI!", `Lô hàng <strong>${lotId}</strong> đã hoàn thành phân phối.`, "Không thể chỉnh sửa hoặc cập nhật lại thông tin.");
                    distViewfinder.classList.remove("success-scan");
                    distScannerPlaceholder.style.display = "block";
                    distScannerSuccess.style.display = "none";
                    return;
                }
                distLotSelect.value = lotId;
                distLotSelect.dispatchEvent(new Event("change"));
            } else {
                showFailureModal("CẬP NHẬT THẤT BẠI!", `Lô hàng <strong>${lotId}</strong> không tồn tại trên hệ thống.`, "Vui lòng kiểm tra lại mã lô hàng hoặc đăng ký mới.");
                distViewfinder.classList.remove("success-scan");
                distScannerPlaceholder.style.display = "block";
                distScannerSuccess.style.display = "none";
            }
        } catch (err) {
            showFailureModal("LỖI HỆ THỐNG!", "Lỗi tải thông tin lô hàng từ máy chủ.", err.message);
        }
    }

    // cfg objects carry mutable stream/raf state
    const transCfg = {
        video: transVideo, laser: transLaser,
        placeholder: transScannerPlaceholder, successEl: transScannerSuccess,
        displayEl: transScannedLotDisplay, lotSelect: transLotSelect,
        viewfinder: transViewfinder, scanCamBtn: btnTransScanCam,
        fileInput: transFileInput,
        currentStream: null, currentRafId: null, stopBtn: null,
        onFound: onTransLotFound,
        stopStream() {
            [this.currentStream, this.currentRafId] = stopStream(
                this.currentStream, this.currentRafId, transVideo, this.stopBtn);
            this.stopBtn = null;
        }
    };
    const distCfg = {
        video: distVideo, laser: distLaser,
        placeholder: distScannerPlaceholder, successEl: distScannerSuccess,
        displayEl: distScannedLotDisplay, lotSelect: distLotSelect,
        viewfinder: distViewfinder, scanCamBtn: btnDistScanCam,
        fileInput: distFileInput,
        currentStream: null, currentRafId: null, stopBtn: null,
        onFound: onDistLotFound,
        stopStream() {
            [this.currentStream, this.currentRafId] = stopStream(
                this.currentStream, this.currentRafId, distVideo, this.stopBtn);
            this.stopBtn = null;
        }
    };

    // ── Bind camera buttons ───────────────────────────────────
    btnTransScanCam.addEventListener("click",  () => startCameraScan(transCfg));
    btnDistScanCam.addEventListener("click",   () => startCameraScan(distCfg));

    // ── Bind file-upload buttons ──────────────────────────────
    btnTransScanFile.addEventListener("click", () => startFileScan(transCfg));
    btnDistScanFile.addEventListener("click",  () => startFileScan(distCfg));

    // Stop camera when user switches tab
    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            if (transCfg.currentStream) transCfg.stopStream();
            if (distCfg.currentStream)  distCfg.stopStream();
        });
    });

    // ── Farmer label buttons ──────────────────────────────────
    btnPrintSimulation.addEventListener("click", () => {
        if (activeLotId) {
            alert(`[MÔ PHỎNG] Tem QR lô '${activeLotId}' đang gửi tới máy in nhiệt...\nHoàn tất! Dán tem lên thùng sản phẩm quýt.`);
        } else {
            alert("Vui lòng khởi tạo lô hàng ở giai đoạn Nông dân trước.");
        }
    });

    // ── Download QR image ─────────────────────────────────────
    document.getElementById("btn-download-qr").addEventListener("click", () => {
        if (!activeLotId) { alert("Chưa có mã QR để tải."); return; }
        const img = farmerLabelQrContainer.querySelector("img");
        if (!img) { alert("Mã QR chưa được tạo."); return; }
        const a = document.createElement("a");
        a.href = img.src;
        a.download = `QR_${activeLotId}.png`;
        a.click();
    });

    // ── "Quét xem thử QR" ─────────────────────────────────────
    btnScanAsConsumerNow.addEventListener("click", () => {
        if (activeLotId) {
            switchTab("consumer");
            consumerSearchInput.value = activeLotId;
            performTrace(activeLotId);
        } else {
            alert("Vui lòng khởi tạo lô hàng ở giai đoạn Nông dân trước.");
        }
    });

    // ── Helper: format date ───────────────────────────────────
    function formatDate(dateStr) {
        if (!dateStr) return "-";
        try {
            const date = new Date(dateStr);
            if (isNaN(date.getTime())) return dateStr;
            return date.toLocaleDateString("vi-VN", { year: 'numeric', month: 'long', day: 'numeric' });
        } catch(e) { return dateStr; }
    }

    // ── Helper: Generate QR Code with custom logo in the center ──
    function generateQrWithLogo(container, text, size = 128, logoUrl = "/static/logo.webp") {
        container.innerHTML = "";
        
        // Create a temporary hidden div to generate the raw QR code
        const tempDiv = document.createElement("div");
        tempDiv.style.display = "none";
        document.body.appendChild(tempDiv);
        
        // Generate QR code using standard QRCode library with high error correction
        new QRCode(tempDiv, {
            text: text,
            width: size * 2, // Generate at 2x resolution for sharpness
            height: size * 2,
            colorDark: "#ff7a00", // Lai Vung Orange
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.H
        });
        
        // We wait a brief moment to ensure QRCode script has synchronously drawn on canvas
        setTimeout(() => {
            const originalCanvas = tempDiv.querySelector("canvas");
            if (!originalCanvas) {
                // Fallback to normal QRCode without logo if something went wrong
                container.innerHTML = "";
                new QRCode(container, {
                    text: text,
                    width: size,
                    height: size,
                    colorDark: "#ff7a00",
                    colorLight: "#ffffff",
                    correctLevel: QRCode.CorrectLevel.H
                });
                if (tempDiv.parentNode) document.body.removeChild(tempDiv);
                return;
            }
            
            // Create a final canvas at 2x resolution to draw high quality logo
            const finalCanvas = document.createElement("canvas");
            const renderSize = size * 2;
            finalCanvas.width = renderSize;
            finalCanvas.height = renderSize;
            
            const ctx = finalCanvas.getContext("2d");
            // Disable image smoothing to keep QR pixel crispness
            ctx.imageSmoothingEnabled = false;
            ctx.drawImage(originalCanvas, 0, 0, renderSize, renderSize);
            
            // Load the logo image
            const img = new Image();
            img.src = logoUrl;
            img.onload = () => {
                const logoSize = renderSize * 0.22; // Logo takes ~22% of QR space
                const logoX = (renderSize - logoSize) / 2;
                const logoY = (renderSize - logoSize) / 2;
                
                // Draw rounded white backdrop for the logo in the center
                const padding = 6;
                const bgX = logoX - padding;
                const bgY = logoY - padding;
                const bgSize = logoSize + padding * 2;
                
                ctx.fillStyle = "#ffffff";
                ctx.beginPath();
                // Draw rounded white square
                const radius = 8;
                ctx.moveTo(bgX + radius, bgY);
                ctx.lineTo(bgX + bgSize - radius, bgY);
                ctx.quadraticCurveTo(bgX + bgSize, bgY, bgX + bgSize, bgY + radius);
                ctx.lineTo(bgX + bgSize, bgY + bgSize - radius);
                ctx.quadraticCurveTo(bgX + bgSize, bgY + bgSize, bgX + bgSize - radius, bgY + bgSize);
                ctx.lineTo(bgX + radius, bgY + bgSize);
                ctx.quadraticCurveTo(bgX, bgY + bgSize, bgX, bgY + bgSize - radius);
                ctx.lineTo(bgX, bgY + radius);
                ctx.quadraticCurveTo(bgX, bgY, bgX + radius, bgY);
                ctx.closePath();
                ctx.fill();
                
                // Draw the logo image rounded inside the white backdrop
                ctx.save();
                ctx.beginPath();
                const logoRadius = 6;
                ctx.moveTo(logoX + logoRadius, logoY);
                ctx.lineTo(logoX + logoSize - logoRadius, logoY);
                ctx.quadraticCurveTo(logoX + logoSize, logoY, logoX + logoSize, logoY + logoRadius);
                ctx.lineTo(logoX + logoSize, logoY + logoSize - logoRadius);
                ctx.quadraticCurveTo(logoX + logoSize, logoY + logoSize, logoX + logoSize - logoRadius, logoY + logoSize);
                ctx.lineTo(logoX + logoRadius, logoY + logoSize);
                ctx.quadraticCurveTo(logoX, logoY + logoSize, logoX, logoY + logoSize - logoRadius);
                ctx.lineTo(logoX, logoY + logoRadius);
                ctx.quadraticCurveTo(logoX, logoY, logoX + logoRadius, logoY);
                ctx.closePath();
                ctx.clip();
                
                ctx.drawImage(img, logoX, logoY, logoSize, logoSize);
                ctx.restore();
                
                // Convert final canvas to dataURL img for seamless download/sharing compatibility
                container.innerHTML = "";
                const finalImg = document.createElement("img");
                finalImg.src = finalCanvas.toDataURL("image/png");
                finalImg.style.display = "block";
                finalImg.style.margin = "0 auto";
                finalImg.style.borderRadius = "8px";
                finalImg.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
                finalImg.style.width = `${size}px`;
                finalImg.style.height = `${size}px`;
                container.appendChild(finalImg);
                
                if (tempDiv.parentNode) document.body.removeChild(tempDiv);
            };
            
            img.onerror = () => {
                // If logo fails to load, fallback to crisp QR code without logo
                container.innerHTML = "";
                const finalImg = document.createElement("img");
                finalImg.src = finalCanvas.toDataURL("image/png");
                finalImg.style.display = "block";
                finalImg.style.margin = "0 auto";
                finalImg.style.borderRadius = "8px";
                finalImg.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
                finalImg.style.width = `${size}px`;
                finalImg.style.height = `${size}px`;
                container.appendChild(finalImg);
                
                if (tempDiv.parentNode) document.body.removeChild(tempDiv);
            };
        }, 50);
    }

    // ============================================================
    // CHATBOT WIDGET FRONTEND LOGIC
    // ============================================================
    
    // DOM Elements
    const chatbotToggleBtn = document.getElementById("chatbot-toggle-btn");
    const chatbotWindow = document.getElementById("chatbot-window");
    const chatbotClearBtn = document.getElementById("chatbot-clear-btn");
    const chatbotCloseBtn = document.getElementById("chatbot-close-btn");
    const chatbotContextBar = document.getElementById("chatbot-context-bar");
    const chatbotContextLabel = document.getElementById("chatbot-context-label");
    const chatbotMessages = document.getElementById("chatbot-messages");
    const chatbotInput = document.getElementById("chatbot-input");
    const chatbotSendBtn = document.getElementById("chatbot-send-btn");

    let chatbotHistory = [];
    let activeLotContext = null;
    let hasChatInitialized = false;

    // Toggle Chat Window
    if (chatbotToggleBtn && chatbotWindow) {
        chatbotToggleBtn.addEventListener("click", () => {
            chatbotWindow.classList.toggle("chatbot-hidden");
            if (!chatbotWindow.classList.contains("chatbot-hidden")) {
                // Focus input field
                if (chatbotInput) chatbotInput.focus();
                
                // Initialize chat if first time opening
                if (!hasChatInitialized) {
                    initializeWelcomeMessage();
                    hasChatInitialized = true;
                }
                
                // Hide badge
                const badge = chatbotToggleBtn.querySelector(".chatbot-badge");
                if (badge) badge.style.display = "none";
            }
        });
    }

    if (chatbotCloseBtn && chatbotWindow) {
        chatbotCloseBtn.addEventListener("click", () => {
            chatbotWindow.classList.add("chatbot-hidden");
        });
    }

    // Clear Chat
    if (chatbotClearBtn) {
        chatbotClearBtn.addEventListener("click", () => {
            if (confirm("Dạ anh/chị có chắc chắn muốn xóa hết lịch sử trò chuyện để bắt đầu phiên mới không ạ?")) {
                chatbotHistory = [];
                initializeWelcomeMessage();
            }
        });
    }

    // Welcome Message
    function initializeWelcomeMessage() {
        if (!chatbotMessages) return;
        chatbotMessages.innerHTML = "";
        appendBotMessage("Dạ em kính chào anh/chị và bà con mình! Em là Trợ lý AI Lai Vung Trace. Em ở đây để giúp anh/chị giải đáp các thắc mắc về Nhật ký canh tác chuẩn VietGAP hay các thông tin xác thực chuỗi khối (Blockchain) của Quýt Hồng Lai Vung nè. Anh/chị cần em hỗ trợ gì cứ nhắn em nhe! 😊");
    }

    // Format text with helper styling
    function formatReplyText(text) {
        let formatted = escapeHtml(text);
        
        // Convert Markdown bold (**text**) to HTML bold
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Convert standard newlines to HTML breaks
        formatted = formatted.replace(/\n/g, '<br>');
        
        return formatted;
    }

    function escapeHtml(text) {
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // ============= TEXT-TO-SPEECH (TTS) SETUP =============
    function initializeTTS() {
        if ('speechSynthesis' in window) {
            // Pre-load voices when available
            window.speechSynthesis.onvoiceschanged = () => {
                console.log("🎙️ Text-to-Speech voices loaded");
            };
        }
    }

    function speakText(text) {
        // Stop any currently playing speech
        if (window.speechSynthesis.speaking) {
            window.speechSynthesis.cancel();
            return;
        }

        // Check browser support
        if (!('speechSynthesis' in window)) {
            alert("Trình duyệt không hỗ trợ tính năng đọc văn bản");
            return;
        }

        const utterance = new SpeechSynthesisUtterance(text);
        
        // Get available voices and find Vietnamese voice
        const voices = window.speechSynthesis.getVoices();
        
        // Prioritize Google Vietnamese voice (most natural), then any Vietnamese voice
        const vietnameseVoice = voices.find(voice => voice.lang === 'vi-VN' && voice.name.includes('Google')) 
                              || voices.find(voice => voice.lang === 'vi-VN')
                              || voices.find(voice => voice.lang.startsWith('vi'));

        if (vietnameseVoice) {
            utterance.voice = vietnameseVoice;
        }

        // Optimize speech parameters
        utterance.rate = 1.0;   // Speed (0.1 to 10)
        utterance.pitch = 1.0;  // Pitch (0 to 2)
        utterance.volume = 1.0; // Volume (0 to 1)

        // Speak
        window.speechSynthesis.speak(utterance);
    }

    // Append Messages to DOM
    function appendBotMessage(text) {
        if (!chatbotMessages) return;
        const msgDiv = document.createElement("div");
        msgDiv.className = "chat-msg bot";
        msgDiv.innerHTML = `
            <div class="chat-msg-avatar"><img src="/static/chatbot.webp" alt="Chatbot" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;"></div>
            <div class="chat-bubble-wrapper">
                <div class="chat-bubble">${formatReplyText(text)}</div>
                <button class="chat-speak-btn" title="Nghe giọng đọc" aria-label="Nghe tin nhắn này">
                    <i class="fa-solid fa-volume-high"></i>
                </button>
            </div>
        `;
        chatbotMessages.appendChild(msgDiv);
        
        // Add click listener to speak button
        const speakBtn = msgDiv.querySelector('.chat-speak-btn');
        const chatBubble = msgDiv.querySelector('.chat-bubble');
        if (speakBtn && chatBubble) {
            speakBtn.addEventListener('click', () => {
                // Extract plain text from chat bubble (removes HTML tags and icons)
                const plainText = chatBubble.textContent || chatBubble.innerText;
                speakText(plainText);
            });
        }
        
        scrollToBottom();
    }

    function appendUserMessage(text) {
        if (!chatbotMessages) return;
        const msgDiv = document.createElement("div");
        msgDiv.className = "chat-msg user";
        msgDiv.innerHTML = `
            <div class="chat-msg-avatar">👤</div>
            <div class="chat-bubble">${escapeHtml(text)}</div>
        `;
        chatbotMessages.appendChild(msgDiv);
        scrollToBottom();
    }

    // Scrolling helper
    function scrollToBottom() {
        if (chatbotMessages) {
            chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
        }
    }

    // Typing indicator
    function showTypingIndicator() {
        if (!chatbotMessages) return null;
        const typingDiv = document.createElement("div");
        typingDiv.className = "chat-msg bot typing-indicator-wrapper";
        typingDiv.innerHTML = `
            <div class="chat-msg-avatar"><img src="/static/chatbot.webp" alt="Chatbot" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;"></div>
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        chatbotMessages.appendChild(typingDiv);
        scrollToBottom();
        return typingDiv;
    }

    function removeTypingIndicator(indicatorDiv) {
        if (indicatorDiv && indicatorDiv.parentNode) {
            indicatorDiv.parentNode.removeChild(indicatorDiv);
        }
    }

    // Auto-resize Input Textarea
    if (chatbotInput) {
        chatbotInput.addEventListener("input", function() {
            this.style.height = "auto";
            this.style.height = (this.scrollHeight) + "px";
            if (this.scrollHeight > 120) {
                this.style.overflowY = "scroll";
                this.style.height = "120px";
            } else {
                this.style.overflowY = "hidden";
            }
        });

        // Enter to Send
        chatbotInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }

    if (chatbotSendBtn) {
        chatbotSendBtn.addEventListener("click", sendChatMessage);
    }

    // Quick replies
    document.querySelectorAll(".quick-reply-chip").forEach(chip => {
        chip.addEventListener("click", () => {
            const msg = chip.getAttribute("data-msg");
            if (msg && chatbotInput) {
                let actualMsg = msg;
                if (msg === "Tóm tắt lô hàng này cho tôi") {
                    if (activeLotId) {
                        actualMsg = `Tóm tắt chi tiết giùm em thông tin lô hàng ${activeLotId} nhe trợ lý!`;
                    } else {
                        actualMsg = "Tóm tắt thông tin lô hàng hiện tại giùm em nhe!";
                    }
                }
                chatbotInput.value = actualMsg;
                sendChatMessage();
            }
        });
    });

    // Send chat message to backend
    async function sendChatMessage() {
        if (!chatbotInput) return;
        const text = chatbotInput.value.trim();
        if (!text) return;

        // Reset input area
        chatbotInput.value = "";
        chatbotInput.style.height = "auto";

        appendUserMessage(text);
        const indicator = showTypingIndicator();

        const payload = {
            message: text,
            history: chatbotHistory,
            context: activeLotContext
        };

        try {
            const response = await fetch("/api/chatbot", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            removeTypingIndicator(indicator);

            if (data.success) {
                appendBotMessage(data.reply);
                
                // Keep only last 10 messages (user + assistant) in history
                chatbotHistory.push({ role: "user", content: text });
                chatbotHistory.push({ role: "assistant", content: data.reply });
                if (chatbotHistory.length > 20) {
                    chatbotHistory = chatbotHistory.slice(-20);
                }
            } else {
                appendBotMessage("Dạ em xin lỗi anh/chị ơi! Hệ thống đang bận xíu, anh/chị bấm gửi lại giùm em nha 🙏");
            }
        } catch (error) {
            console.error("Chatbot API Error:", error);
            removeTypingIndicator(indicator);
            appendBotMessage("Dạ em xin lỗi anh/chị ơi, đường truyền mạng có chút trục trặc. Anh/chị kiểm tra kết nối mạng và thử lại sau nha 😢");
        }
    }

    // Global hooks to receive lot context updates
    window.updateChatbotLotContext = function(traceData) {
        if (!chatbotContextBar || !chatbotContextLabel) return;
        
        if (!traceData || !traceData.data) {
            window.clearChatbotLotContext();
            return;
        }

        const lotId = traceData.data.lot_id || activeLotId;
        const farmer = traceData.data.farmer;
        const transporter = traceData.data.transporter;
        const distributor = traceData.data.distributor;
        const verify = traceData.blockchain_verification;

        chatbotContextLabel.textContent = `Đang tư vấn về lô hàng: ${lotId}`;
        chatbotContextBar.classList.add("active");

        // Format rich context string for the AI LLM
        let ctx = `[CONTEXT LÔ HÀNG ${lotId}]\n`;
        ctx += `Mã Lô hàng: ${lotId}\n`;
        ctx += `- Giống quýt: ${farmer.variety || "Quýt Hồng Lai Vung"}\n`;
        ctx += `- Ngày trồng: ${farmer.planting_date || "Không rõ"}, Ngày thu hoạch: ${farmer.harvest_date || "Không rõ"}\n`;
        ctx += `- Sản lượng thu hoạch: ${farmer.yield_kg || 0} kg, Đạt chuẩn chất lượng: ${farmer.quality || "VietGAP"}\n`;
        ctx += `- Phân bón sử dụng: ${farmer.fertilizer || "Không dùng"}, Thuốc bảo vệ thực vật: ${farmer.pesticide || "Không dùng"}\n`;
        ctx += `- Trạng thái xác thực Blockchain Farmer: ${verify.farmer.verified ? "HỢP LỆ VÀ TOÀN VẸN" : "CẢNH BÁO GIẢ MẠO (LỆCH HASH!)"}\n`;

        if (transporter) {
            ctx += `- Ngày nhận vận chuyển: ${transporter.pickup_date}, Ngày giao: ${transporter.delivery_date}\n`;
            ctx += `- Nhiệt độ xe lạnh bảo quản: ${transporter.temperature}°C, Trạng thái: ${transporter.condition}\n`;
            ctx += `- Thời gian di chuyển: ${transporter.transit_time}\n`;
            ctx += `- Trạng thái xác thực Blockchain Logistics: ${verify.transporter.verified ? "HỢP LỆ VÀ TOÀN VẸN" : "CẢNH BÁO GIẢ MẠO (LỆCH HASH!)"}\n`;
        } else {
            ctx += `- Vận chuyển: Chưa có dữ liệu giao nhận trên Blockchain.\n`;
        }

        if (distributor) {
            ctx += `- Ngày nhập kho bán lẻ: ${distributor.warehouse_date}, Ngày phân phối ra thị trường: ${distributor.retail_date}\n`;
            ctx += `- Hạn dùng đề xuất: ${distributor.shelf_life_expiry || "Chưa tính"}\n`;
            ctx += `- Điều kiện bảo quản tại quầy: ${distributor.storage_condition}\n`;
            ctx += `- Trạng thái xác thực Blockchain Nhà phân phối: ${verify.distributor.verified ? "HỢP LỆ VÀ TOÀN VẸN" : "CẢNH BÁO GIẢ MẠO (LỆCH HASH!)"}\n`;
        } else {
            ctx += `- Phân phối: Chưa có thông tin phân phối lẻ.\n`;
        }

        ctx += `- Cảnh báo xâm nhập cơ sở dữ liệu (SQLite Tampered check): ${verify.is_tampered ? "DỮ LIỆU ĐÃ BỊ SỬA ĐỔI TRÁI PHÉP KHÔNG KHỚP VỚI CHUỖI KHỐI!" : "AN TOÀN TUYỆT ĐỐI"}\n`;
        
        activeLotContext = ctx;

        // If the chatbot window is open, highlight the new context with a visual pulse
        if (chatbotWindow && !chatbotWindow.classList.contains("chatbot-hidden")) {
            chatbotContextBar.style.animation = "none";
            setTimeout(() => {
                chatbotContextBar.style.animation = "chatPulse 1s ease-in-out";
            }, 10);
        } else {
            // Show a badge on chatbot toggle to show we have new information loaded
            const badge = chatbotToggleBtn ? chatbotToggleBtn.querySelector(".chatbot-badge") : null;
            if (badge) {
                badge.style.display = "block";
                badge.style.animation = "statusBlink 1.5s ease-in-out infinite";
            }
        }
    };

    window.clearChatbotLotContext = function() {
        activeLotContext = null;
        if (chatbotContextLabel) chatbotContextLabel.textContent = `Đang tư vấn về lô hàng: -`;
        if (chatbotContextBar) chatbotContextBar.classList.remove("active");
    };

    // Initialize Text-to-Speech on page load
    initializeTTS();
});

