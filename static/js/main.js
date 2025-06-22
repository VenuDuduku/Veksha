// main.js - E-Commerce Store

$(document).ready(function() {
    // Real-time cart count update
    function updateCartCount() {
        $.get('/api/cart_count')
            .done(function(data) {
                $('#cartCount').text(data.count);
            });
    }

    // Real-time cart total update (if needed)
    function updateCartTotal() {
        $.get('/api/cart_total')
            .done(function(data) {
                $('#cartTotal').text('$' + data.total.toFixed(2));
            });
    }

    // Call on page load if user is authenticated
    if ($('#cartCount').length) {
        updateCartCount();
    }
    if ($('#cartTotal').length) {
        updateCartTotal();
    }

    // Optional: Add fade-in animation to main content
    $('main.container').addClass('fade-in');

    // Optional: Show loading spinner on form submit
    $('form').on('submit', function() {
        $(this).find('button[type=submit]').append(' <span class="loading"></span>');
    });

    // Search functionality enhancements
    const searchInput = $('input[name="search"], input[name="q"]');
    const searchForm = $('form[action*="index"], form[action*="search"]');
    
    // Auto-submit search on Enter key
    searchInput.on('keypress', function(e) {
        if (e.which === 13) { // Enter key
            e.preventDefault();
            searchForm.submit();
        }
    });

    // Search suggestions (if you want to add auto-complete later)
    searchInput.on('input', function() {
        const query = $(this).val();
        if (query.length >= 2) {
            // You can add AJAX call here for search suggestions
            // For now, we'll just highlight the search box
            $(this).addClass('is-valid');
        } else {
            $(this).removeClass('is-valid');
        }
    });

    // Clear search functionality
    $('.btn-clear-search').on('click', function() {
        searchInput.val('');
        searchForm.submit();
    });

    // Category filter change auto-submit
    $('select[name="category"]').on('change', function() {
        if ($(this).val() !== '') {
            searchForm.submit();
        }
    });

    // Search result highlighting
    function highlightSearchTerms() {
        const urlParams = new URLSearchParams(window.location.search);
        const searchQuery = urlParams.get('search') || urlParams.get('q');
        
        if (searchQuery) {
            $('.card-title, .card-text').each(function() {
                const text = $(this).text();
                const highlightedText = text.replace(
                    new RegExp(searchQuery, 'gi'),
                    '<mark class="bg-warning">$&</mark>'
                );
                $(this).html(highlightedText);
            });
        }
    }

    // Apply search highlighting
    highlightSearchTerms();

    // Quick search from navigation
    $('.navbar .input-group input').on('keypress', function(e) {
        if (e.which === 13) {
            e.preventDefault();
            const query = $(this).val();
            if (query.trim()) {
                window.location.href = '/?search=' + encodeURIComponent(query);
            }
        }
    });

    // Search analytics (optional - for tracking popular searches)
    searchForm.on('submit', function() {
        const searchQuery = searchInput.val();
        if (searchQuery) {
            console.log('Search performed:', searchQuery);
            // You can add analytics tracking here
        }
    });
}); 