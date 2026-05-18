let sortDirections = {};

function parseSortValue(value) {
    if (value === null || value === undefined || value === "") {
        return null;
    }

    const numberValue = Number(value);

    if (!Number.isNaN(numberValue)) {
        return numberValue;
    }

    return value.toLowerCase();
}

function updateSortIndicators(activeColumnIndex, direction) {
    const table = document.getElementById("vm-report-table");
    const headers = table.tHead.rows[0].cells;

    for (let i = 0; i < headers.length; i++) {
        const indicator = headers[i].querySelector(".sort-indicator");

        if (indicator === null) {
            continue;
        }

        indicator.textContent =
            i === activeColumnIndex
                ? direction === "asc"
                    ? "▲"
                    : "▼"
                : "";
    }
}

function sortTable(columnIndex) {
    const table = document.getElementById("vm-report-table");
    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);

    const currentDirection = sortDirections[columnIndex] || "asc";
    const nextDirection = currentDirection === "asc" ? "desc" : "asc";

    sortDirections = {};
    sortDirections[columnIndex] = nextDirection;

    rows.sort((rowA, rowB) => {
        const valueA = parseSortValue(
            rowA.cells[columnIndex].getAttribute("data-sort-value")
        );

        const valueB = parseSortValue(
            rowB.cells[columnIndex].getAttribute("data-sort-value")
        );

        if (valueA === null && valueB === null) {
            return 0;
        }

        if (valueA === null) {
            return 1;
        }

        if (valueB === null) {
            return -1;
        }

        if (valueA < valueB) {
            return nextDirection === "asc" ? -1 : 1;
        }

        if (valueA > valueB) {
            return nextDirection === "asc" ? 1 : -1;
        }

        return 0;
    });

    rows.forEach((row) => tbody.appendChild(row));

    updateSortIndicators(columnIndex, nextDirection);
}