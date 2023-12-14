// toggle showing all authors
function toggleAuthors(event) {
      event.preventDefault();
      const moreLink = event.target;
      const moreAuthors = moreLink.parentElement.querySelector('.more-authors');
      console.log(moreAuthors);
      moreAuthors.style.display = 'inline';
      moreLink.textContent = '';
}

// update the dom with papers
function populatePapers(papersData, clear_old_papers=true) {
    var papersContainer = document.getElementById("papers-container");
    if (clear_old_papers) {
        papersContainer.innerHTML = '';
        all_papers = [];
        papers_displayed = papersData.length;
    }
    else {
        papers_displayed += papersData.length;
    }

    if (papersData.length === 0 && clear_old_papers) {
      papersContainer.innerHTML = "<br><br><p class='text-center'>No papers found.<br><br><a class='btn btn-sm btn-select' href='/'><span class='mdi mdi-refresh'></span> Reset</a></p>";
      return;
    }
    else if (papersData.length === 0) {
      active_query = false;
    }
    for (var i = 0; i < papersData.length; i++) {
        if (all_papers.includes(papersData[i].arxiv_id)) {
            continue;
        }
      var paper = papersData[i];
      var paperHTML = `
  <div class="card">
    <a class="paper-link" href="https://arxiv.org/abs/${paper.arxiv_id}" target="_blank">
      <img src="${paper.image_url}" class="card-img-top" alt="Paper Image">
      <div class="card-body d-flex flex-column">
        <div class="card-title">${paper.title}</div>
        <p class="card-text paper-summary">${paper.summary}
          </p>
        <div class="mt-auto">
          <p class="card-text">
            <span class="authors-group">
              <span class="first-author">
                <button type="button" class="btn btn-xs btn-secondary author-btn" onclick="handleAuthorClick(event)">
                  <span class="mdi mdi-account"></span> ${paper.authors[0]}
                </button>
              </span>
              ${paper.authors.slice(1, 10).map(author => `
                <span class="author-item">
                  <button type="button" class="btn btn-xs btn-secondary author-btn" onclick="handleAuthorClick(event)">
                    <span class="mdi mdi-account"></span> ${author}
                  </button>
                </span>
              `).join('')}
            </span>
            ${paper.authors.length > 10
              ? `
                <span class="more-authors">
                  ${paper.authors.slice(10).map(author => `
                      <span class="author-item">
                        <button type="button" class="btn btn-xs btn-secondary author-btn" onclick="handleAuthorClick(event)">
                          <span class="mdi mdi-account"></span> ${author}
                        </button>
                      </span>
                    `).join('')}
                </span>
                <span class="more-link" onclick="toggleAuthors(event)">show all</span>
                `
              : ''}
          </p>
        </div>
      </div>
      <br>
      <br>
      </a>
      <div class="card-footer">
        <div class="d-flex justify-content-between">
            <div>
                <span title="Paper citations" class="paper-citations"><span class="mdi mdi-star"></span> ${paper.citations.toLocaleString()}</span>
                &nbsp;
                <a target="_blank" class="link-nocolor" href="https://arxiv.org/pdf/${paper.arxiv_id}" title="Download this paper as a pdf"><span class="mdi mdi-image"></span></a>
                <a target="_blank" class="link-nocolor" href="https://arxiv-vanity.com/papers/${paper.arxiv_id}" title="View this paper as a webpage on arxiv-vanity"><span class="mdi mdi-image-outline"></span></a>
                <a target="_blank" class="link-nocolor" href="https://scholar.google.com/scholar?hl=en&q=%22${encodeURIComponent(paper.title)}%22&btnG" title="Search for this paper on Google Scholar"><span class="mdi mdi-google"></span></a>
            </div>
            <div>
                <span title="The date the paper was first published onto arxiv" class="paper-date">
                    <span class="mdi mdi-calendar-clock"></span>
                    ${formatPublicationDate(paper.publication_date)}
                </span>
            </div>
        </div>
      </div>
  </div>
`;
      papersContainer.insertAdjacentHTML('beforeend', paperHTML);
      all_papers.push(paper.arxiv_id);
    }
}

// format paper publication date
function formatPublicationDate(dateString) {
  const options = { year: 'numeric', month: 'long', day: 'numeric' };
  const formattedDate = new Date(dateString).toLocaleDateString(undefined, options);
  return formattedDate;
}

// update the present papers
function update(query=null, delete_old_papers=true) {
    if (query) {
      var url = '/api/papers/?q=' + encodeURIComponent(query) + '&d=' + date_range;
    }
    else {
        var url = '/api/papers/?d=' + date_range;
    }
    if (!delete_old_papers) {
        url += '&s=' + papers_displayed;
    }
      fetch(url)
        .then(response => response.json())
        .then(data => populatePapers(data, delete_old_papers))
        .catch(error => {
            alert("Error fetching papers. Please try again later.");
            console.error("Error fetching papers:", error);
        });
}

// show all authors button
function handleAuthorClick(event) {
    event.preventDefault();
    const authorName = event.target.textContent.trim();
    const searchInput = document.getElementById("search-input");
    searchInput.value = authorName;
    update(authorName);
    $('#reset-btn').addClass("show");
}

$(document).ready(function() {
    date_range = 'this-month';
    papers_displayed = 0;
    active_query = true;
    var all_papers = [];

    setTimeout(function() {
        $('#search-input').focus();
    }, 350);

    update();

    // search box reset button
    var searchBox = $("#search-input");
    var resetButton = $("#reset-btn");
    resetButton.on("click", function() {
        searchBox.val("");
        $('#reset-btn').removeClass("show");
        update();
    });

    // on search box hover
    const myInput = document.getElementById("search-input");
    myInput.addEventListener("focus", function() {
        search_input = document.getElementById("search-input").value;
        if (search_input) {
            $('#reset-btn').addClass("show");
        }
    });


    // auto-search on enter key
    document.getElementById("search-input").addEventListener("keydown", function(event) {
        if (event.key === 'Enter') {
            active_query = true;
            var searchInput = event.target.value;
            $('#reset-btn').removeClass("show");
            document.getElementById("search-input").blur();
            update(searchInput);
        }
    });

    // auto-search after typing stops
    var typingTimer;
    var doneTypingInterval = 350;
    document.getElementById("search-input").addEventListener("keyup", function(event) {
        var searchInput = event.target.value;
        if (searchInput) {
            $('#reset-btn').addClass("show");
        }
        else {
            $('#reset-btn').removeClass("show");
        }
       active_query = true;
      clearTimeout(typingTimer);
      typingTimer = setTimeout(function() {
        var searchInput = event.target.value;
        update(searchInput);
      }, doneTypingInterval);
    });

    // date buttons
    $('#selection-buttons').on('click', 'button', function() {
        active_query = true;
        $('#selection-buttons button').removeClass('active');
        $(this).addClass('active');
        var selectedValue = $(this).data('value');
        date_range = selectedValue;
        search_input = document.getElementById("search-input").value;
        update(search_input);
    });

      window.addEventListener('scroll', function() {
      if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 250) {
          if (active_query) {
            search_input = document.getElementById("search-input").value;
            update(search_input, false);
          }
      }
    });
});