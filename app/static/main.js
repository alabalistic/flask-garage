// main.js
document.addEventListener('DOMContentLoaded', (event) => {
    document.querySelectorAll('.view-all-comments').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const postId = this.getAttribute('data-post-id');
            document.querySelector(`#comments-${postId} .collapse-comments`).style.display = 'block';
            this.style.display = 'none';
        });
    });

    document.querySelectorAll('.collapse-comments').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const postId = this.getAttribute('data-post-id');
            document.querySelector(`#comments-${postId} .view-all-comments`).style.display = 'block';
            this.style.display = 'none';
        });
    });
});
