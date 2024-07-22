document.addEventListener('DOMContentLoaded', function() {
    const viewAllLinks = document.querySelectorAll('.view-all-comments');
    const collapseLinks = document.querySelectorAll('.collapse-comments');

    viewAllLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();
            const postId = this.dataset.postId;
            const commentsSection = document.querySelector(`#comments-${postId}`);

            if (!commentsSection) {
                console.error(`No comments section found for post ID: ${postId}`);
                return;
            }

            // Make an AJAX request to get all comments for the post
            fetch(`/post/${postId}/comments`)
                .then(response => response.json())
                .then(data => {
                    commentsSection.innerHTML = ''; // Clear existing comments
                    data.comments.forEach(comment => {
                        const commentHtml = `
                            <div class="media mt-3">
                                <img class="rounded-circle comment-img" src="/static/profile_pics/${comment.author.image_file}">
                                <div class="media-body">
                                    <h6 class="mt-0">${comment.author.username}</h6>
                                    ${comment.content}
                                    <small class="text-muted">${comment.date_posted}</small>
                                </div>
                            </div>
                        `;
                        commentsSection.innerHTML += commentHtml;
                    });
                    const viewAllLink = document.querySelector(`.view-all-comments[data-post-id="${postId}"]`);
                    const collapseLink = document.querySelector(`.collapse-comments[data-post-id="${postId}"]`);

                    if (viewAllLink) {
                        viewAllLink.style.display = 'none';
                    } else {
                        console.error(`No view-all-comments link found for post ID: ${postId}`);
                    }

                    if (collapseLink) {
                        collapseLink.style.display = 'block';
                    } else {
                        console.error(`No collapse-comments link found for post ID: ${postId}`);
                    }
                })
                .catch(error => console.error('Error fetching comments:', error));
        });
    });

    collapseLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();
            const postId = this.dataset.postId;
            const commentsSection = document.querySelector(`#comments-${postId}`);

            if (!commentsSection) {
                console.error(`No comments section found for post ID: ${postId}`);
                return;
            }

            // Fetch first 2 comments again (assuming these are available in the initial HTML)
            fetch(`/post/${postId}/comments?limit=2`)
                .then(response => response.json())
                .then(data => {
                    commentsSection.innerHTML = ''; // Clear existing comments
                    data.comments.slice(0, 2).forEach(comment => {
                        const commentHtml = `
                            <div class="media mt-3">
                                <img class="rounded-circle comment-img" src="/static/profile_pics/${comment.author.image_file}">
                                <div class="media-body">
                                    <h6 class="mt-0">${comment.author.username}</h6>
                                    ${comment.content}
                                    <small class="text-muted">${comment.date_posted}</small>
                                </div>
                            </div>
                        `;
                        commentsSection.innerHTML += commentHtml;
                    });
                    const viewAllLink = document.querySelector(`.view-all-comments[data-post-id="${postId}"]`);
                    const collapseLink = document.querySelector(`.collapse-comments[data-post-id="${postId}"]`);

                    if (collapseLink) {
                        collapseLink.style.display = 'none';
                    } else {
                        console.error(`No collapse-comments link found for post ID: ${postId}`);
                    }

                    if (viewAllLink) {
                        viewAllLink.style.display = 'block';
                    } else {
                        console.error(`No view-all-comments link found for post ID: ${postId}`);
                    }
                })
                .catch(error => console.error('Error fetching comments:', error));
        });
    });
});
