<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<!DOCTYPE html>
<html>
<head>
    <title>상품 관리</title>
    <script>
        const PRODUCT_API = 'http://localhost:8080/api/products';
        const CART_API = 'http://localhost:8080/api/cart';
        const ORDER_API = 'http://localhost:8080/api/orders';

        // 상품 API
        const productApi = {
            // 상품 목록 조회
            list: async (category, page = 1, limit = 10) => {
                const url = `${PRODUCT_API}?category=${category}&page=${page}&limit=${limit}`;
                const response = await fetch(url);
                return response.json();
            },

            // 상품 상세 조회
            get: async (productId) => {
                const response = await fetch(`${PRODUCT_API}/${productId}`);
                return response.json();
            },

            // 상품 검색 (SQL Injection 취약점)
            search: async (query) => {
                const response = await fetch(`${PRODUCT_API}/search?q=${query}`);
                return response.json();
            },

            // 상품 생성 (관리자 전용)
            create: async (product) => {
                const response = await fetch(PRODUCT_API, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(product)
                });
                return response.json();
            },

            // 상품 업데이트
            update: async (productId, updates) => {
                const response = await fetch(`${PRODUCT_API}/${productId}`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(updates)
                });
                return response.json();
            },

            // 상품 삭제
            delete: async (productId) => {
                const response = await fetch(`${PRODUCT_API}/${productId}`, {
                    method: 'DELETE'
                });
                return response.json();
            },

            // 리뷰 조회
            getReviews: async (productId) => {
                const response = await fetch(`${PRODUCT_API}/${productId}/reviews`);
                return response.json();
            },

            // 리뷰 작성 (XSS 취약점)
            addReview: async (productId, review) => {
                const response = await fetch(`${PRODUCT_API}/${productId}/reviews`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(review)
                });
                return response.json();
            }
        };

        // 장바구니 API
        const cartApi = {
            // 장바구니 조회
            get: () => fetch(CART_API).then(r => r.json()),

            // 장바구니에 추가
            add: (productId, quantity) => fetch(`${CART_API}/add`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({product_id: productId, quantity: quantity})
            }).then(r => r.json()),

            // 장바구니 항목 업데이트
            update: (itemId, quantity) => fetch(`${CART_API}/items/${itemId}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({quantity: quantity})
            }).then(r => r.json()),

            // 장바구니 항목 삭제
            remove: (itemId) => fetch(`${CART_API}/items/${itemId}`, {
                method: 'DELETE'
            }).then(r => r.json()),

            // 장바구니 비우기
            clear: () => fetch(`${CART_API}/clear`, {method: 'POST'}).then(r => r.json())
        };

        // 주문 API
        const orderApi = {
            // 주문 생성
            create: (cartId, shippingAddress, paymentMethod) =>
                fetch(ORDER_API, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        cart_id: cartId,
                        shipping_address: shippingAddress,
                        payment_method: paymentMethod
                    })
                }).then(r => r.json()),

            // 주문 목록 조회
            list: () => fetch(ORDER_API).then(r => r.json()),

            // 주문 상세 조회
            get: (orderId) => fetch(`${ORDER_API}/${orderId}`).then(r => r.json()),

            // 주문 취소
            cancel: (orderId) => fetch(`${ORDER_API}/${orderId}/cancel`, {
                method: 'POST'
            }).then(r => r.json()),

            // 주문 상태 업데이트 (관리자)
            updateStatus: (orderId, status) => fetch(`${ORDER_API}/${orderId}/status`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({status: status})
            }).then(r => r.json())
        };

        // 상품 목록 로드
        async function loadProducts(category = 'all') {
            try {
                const products = await productApi.list(category);
                displayProducts(products);
            } catch (error) {
                console.error('상품 로드 실패:', error);
            }
        }

        // 상품 표시
        function displayProducts(products) {
            const container = document.getElementById('productList');
            container.innerHTML = '';

            products.forEach(product => {
                const div = document.createElement('div');
                div.className = 'product-item';
                div.innerHTML = `
                    <h3>${product.name}</h3>
                    <p>${product.description}</p>
                    <p>가격: ${product.price}원</p>
                    <button onclick="addToCart(${product.id})">장바구니 담기</button>
                    <button onclick="viewProduct(${product.id})">상세보기</button>
                `;
                container.appendChild(div);
            });
        }

        // 장바구니에 추가
        async function addToCart(productId) {
            try {
                await cartApi.add(productId, 1);
                alert('장바구니에 추가되었습니다.');
                updateCartCount();
            } catch (error) {
                console.error('장바구니 추가 실패:', error);
            }
        }

        // 상품 검색
        async function searchProducts() {
            const query = document.getElementById('searchInput').value;
            try {
                const results = await productApi.search(query);
                displayProducts(results);
            } catch (error) {
                console.error('검색 실패:', error);
            }
        }

        // 리뷰 작성
        async function submitReview(productId) {
            const review = {
                rating: document.getElementById('rating').value,
                comment: document.getElementById('comment').value,
                user_id: localStorage.getItem('user_id')
            };

            try {
                await productApi.addReview(productId, review);
                alert('리뷰가 작성되었습니다.');
                loadReviews(productId);
            } catch (error) {
                console.error('리뷰 작성 실패:', error);
            }
        }

        // XMLHttpRequest를 사용한 추천 상품 로드
        function loadRecommendations() {
            const xhr = new XMLHttpRequest();
            xhr.open('GET', PRODUCT_API + '/recommendations', true);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    const recommendations = JSON.parse(xhr.responseText);
                    displayRecommendations(recommendations);
                }
            };
            xhr.send();
        }

        // jQuery 스타일 API 호출
        function jqueryStyleGetProducts() {
            const request = new XMLHttpRequest();
            request.open('GET', PRODUCT_API + '/trending', true);
            request.onreadystatechange = function() {
                if (request.readyState === 4 && request.status === 200) {
                    const trending = JSON.parse(request.responseText);
                    console.log('인기 상품:', trending);
                }
            };
            request.send();
        }

        // 페이지 로드 시 실행
        window.onload = () => {
            loadProducts();
            loadRecommendations();
            jqueryStyleGetProducts();
        };
    </script>
</head>
<body>
    <h1>상품 목록</h1>

    <div>
        <input type="text" id="searchInput" placeholder="상품 검색" />
        <button onclick="searchProducts()">검색</button>
    </div>

    <div>
        <button onclick="loadProducts('electronics')">전자제품</button>
        <button onclick="loadProducts('clothing')">의류</button>
        <button onclick="loadProducts('books')">도서</button>
        <button onclick="loadProducts('all')">전체</button>
    </div>

    <div id="productList"></div>

    <div id="recommendations"></div>
</body>
</html>
