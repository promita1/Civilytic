(function () {
  "use strict";

  var MAX_MEMBERS = 12;

  var RELATIONSHIPS = [
    ["self", "You"],
    ["partner", "Spouse or common-law partner"],
    ["child", "Child"],
    ["parent", "Parent"],
    ["other", "Other"],
  ];
  var STATUSES = [
    ["", "Choose..."],
    ["citizen", "Canadian citizen"],
    ["pr", "Permanent resident"],
    ["study_permit", "Study permit holder"],
    ["work_permit", "Work permit holder"],
    ["visitor", "Visitor"],
    ["refugee_claimant", "Refugee claimant"],
    ["protected_person", "Protected person"],
    ["other", "Other"],
  ];
  var NOT_SURE = [["", "Not sure"], ["true", "Yes"], ["false", "No"]];

  var OUTCOMES = {
    may_qualify: { label: "May qualify", css: "ok" },
    needs_info: { label: "Needs more information", css: "info" },
    does_not_qualify: { label: "Does not appear to qualify", css: "no" },
  };
  var ORDER = { may_qualify: 0, needs_info: 1, does_not_qualify: 2 };
  var MARKS = {
    met: "\u2713 Met",
    not_met: "\u2717 Not met",
    unknown: "? Unknown",
  };

  var form = document.getElementById("check-form");
  var membersBox = document.getElementById("members");
  var resultsBox = document.getElementById("results");
  var errorBox = document.getElementById("error");
  var submitButton = document.getElementById("submit");
  var addButton = document.getElementById("add-member");
  var today = new Date().toISOString().slice(0, 10);

  // Builds an element. Text is always set with textContent, never as HTML.
  function el(tag, props) {
    var node = document.createElement(tag);
    var keys = Object.keys(props || {});
    keys.forEach(function (key) {
      if (key === "class") node.className = props[key];
      else if (key === "text") node.textContent = props[key];
      else node.setAttribute(key, props[key]);
    });
    for (var i = 2; i < arguments.length; i++) {
      if (arguments[i]) node.append(arguments[i]);
    }
    return node;
  }

  function select(name, options, selected) {
    var node = el("select", { name: name });
    options.forEach(function (pair) {
      var option = el("option", { value: pair[0], text: pair[1] });
      if (pair[0] === selected) option.selected = true;
      node.append(option);
    });
    return node;
  }

  function field(labelText, control) {
    return el("label", {}, labelText, control);
  }

  function addMember(isSelf) {
    var row = el("fieldset", { class: "member" });
    row.append(el("legend", { text: isSelf ? "You" : "Another person" }));

    if (isSelf) {
      row.append(el("input", { type: "hidden", name: "relationship", value: "self" }));
    } else {
      row.append(
        field(
          "Relationship to you",
          select(
            "relationship",
            RELATIONSHIPS.filter(function (r) { return r[0] !== "self"; }),
            "partner"
          )
        )
      );
    }

    row.append(
      field("Date of birth", el("input", { type: "date", name: "birth_date", max: today, required: "" })),
      field("Immigration status", select("status", STATUSES, "")),
      field(
        "Years lived in Canada since age 18 (optional)",
        el("input", { type: "number", name: "years", min: "0", max: "120", step: "1" })
      ),
      field("Resident of Canada for income tax purposes?", select("tax_resident", NOT_SURE, "")),
      field("Receives the Old Age Security pension?", select("receives_oas", NOT_SURE, ""))
    );
    row.querySelector('[name="status"]').setAttribute("required", "");

    if (!isSelf) {
      var remove = el("button", { type: "button", class: "link", text: "Remove this person" });
      remove.addEventListener("click", function () {
        row.remove();
        addButton.disabled = false;
      });
      row.append(remove);
    }
    membersBox.append(row);
  }

  function readMember(row) {
    function get(name) { return row.querySelector('[name="' + name + '"]'); }
    function tri(value) { return value === "" ? null : value === "true"; }
    var years = get("years").value;
    return {
      relationship: get("relationship").value,
      birth_date: get("birth_date").value,
      immigration_status: get("status").value,
      years_in_canada: years === "" ? null : Number(years),
      is_tax_resident: tri(get("tax_resident").value),
      receives_oas: tri(get("receives_oas").value),
    };
  }

  function describeError(data, status) {
    if (status === 429) return "Too many requests. Please wait a minute and try again.";
    var parts = [];
    (function walk(value, path) {
      if (typeof value === "string") parts.push(path ? path + ": " + value : value);
      else if (Array.isArray(value)) value.forEach(function (v) { walk(v, path); });
      else if (value && typeof value === "object") {
        Object.keys(value).forEach(function (k) {
          walk(value[k], path ? path + " " + k : k);
        });
      }
    })(data, "");
    return parts.join(" ") || "Something went wrong.";
  }

  function renderRules(rules) {
    var list = el("ul", { class: "rules" });
    var seenGroups = {};
    rules.forEach(function (rule) {
      if (rule.group && !seenGroups[rule.group]) {
        seenGroups[rule.group] = true;
        list.append(el("li", { class: "group-label", text: "Any one of these is enough:" }));
      }
      var item = el("li", { class: "rule " + rule.status + (rule.group ? " grouped" : "") });
      item.append(el("span", { class: "mark", text: MARKS[rule.status] }));
      item.append(document.createTextNode(rule.description));
      list.append(item);
    });
    return list;
  }

  function renderProgram(program) {
    var info = OUTCOMES[program.outcome];
    var card = el("article", { class: "program " + info.css });

    var head = el("div", { class: "program-head" });
    head.append(el("h3", { text: program.program }));
    head.append(el("span", { class: "badge " + info.css, text: info.label }));
    card.append(head);

    if (program.summary) card.append(el("p", { class: "summary", text: program.summary }));

    var details = el("details");
    if (program.outcome !== "does_not_qualify") details.open = true;
    details.append(el("summary", { text: "Conditions checked" }));
    details.append(renderRules(program.rules));
    card.append(details);

    var source = el("p", { class: "source" });
    if (typeof program.source_url === "string" && program.source_url.indexOf("https://") === 0) {
      source.append(
        el("a", {
          href: program.source_url,
          target: "_blank",
          rel: "noopener noreferrer",
          text: "Official source",
        })
      );
    }
    source.append(
      document.createTextNode(
        " \u00b7 " +
          (program.last_verified
            ? "Last verified " + program.last_verified
            : "Not yet verified by a person")
      )
    );
    card.append(source);
    return card;
  }

  function renderResults(data) {
    var fragment = document.createDocumentFragment();
    data.people.forEach(function (person) {
      var section = el("section", { class: "person" });
      section.append(el("h2", { text: person.person }));
      var programs = person.programs.slice().sort(function (a, b) {
        return ORDER[a.outcome] - ORDER[b.outcome];
      });
      if (programs.length === 0) {
        section.append(el("p", { text: "No programs are loaded for this household yet." }));
      }
      programs.forEach(function (program) { section.append(renderProgram(program)); });
      fragment.append(section);
    });
    fragment.append(el("p", { class: "disclaimer", text: data.disclaimer }));
    resultsBox.replaceChildren(fragment);
    resultsBox.scrollIntoView({ behavior: "smooth" });
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    errorBox.textContent = "";
    var income = document.getElementById("income").value;
    var payload = {
      province: document.getElementById("province").value,
      household_income: income === "" ? null : Number(income),
      members: Array.prototype.map.call(membersBox.querySelectorAll(".member"), readMember),
    };
    submitButton.disabled = true;
    fetch("/api/check/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (response) {
        return response.json().then(function (data) {
          return { ok: response.ok, status: response.status, data: data };
        });
      })
      .then(function (result) {
        if (!result.ok) {
          resultsBox.replaceChildren();
          errorBox.textContent = describeError(result.data, result.status);
        } else {
          renderResults(result.data);
        }
      })
      .catch(function () {
        errorBox.textContent = "Could not reach the server. Please try again.";
      })
      .finally(function () {
        submitButton.disabled = false;
      });
  });

  addButton.addEventListener("click", function () {
    addMember(false);
    if (membersBox.querySelectorAll(".member").length >= MAX_MEMBERS) {
      addButton.disabled = true;
    }
  });

  addMember(true);
})();