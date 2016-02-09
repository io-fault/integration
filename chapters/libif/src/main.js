function
select_identifier(element)
{
	
}

function
select_path(element)
{
	
}

function
highlight(element)
{
	Prism.highlightElement(element, undefined, undefined);
}

function
reference_link(source, module, name)
{
	if (source == "builtin")
	{
		return "http://docs.python.org/3/library/" + module;
	}
	else if (source == "project-local")
	{
		if (module == documented_module)
			return "#" + name;
		else
			return module + "#" + name;
	}
	else
	{
		return "";
	}
}

/* current source code display state */
window.source_code_display = null;
window.source_context_quantity = 0;

function
collapse(element)
{
	if (!element.className.endsWith(" collapsed"))
	{
		el.className = el.className + " collapsed";
	}
}

function
reveal(element)
{
	if (element.className.endsWith(" collapsed"))
	{
		var idx = element.className.lastIndexOf(" collapsed");
		element.className = element.className.substring(0, idx);
	}
}

function
toggle_collapsed(event)
{
	var el = event.target;

	while (el.getAttribute("ondblclick") == null)
		el = el.parentNode;

	if (el.className.endsWith(' collapsed'))
	{
		el.className = el.className.substring(0, el.className.lastIndexOf(' collapsed'));
	}
	else
	{
		el.className = el.className + ' collapsed';
	}
}

function
hashchanged()
{
	var nid = window.location.hash.slice(1); /* strip preceding '#' */
	var description = document.getElementById("subject.description.");
	var current = document.getElementById("subject.description.element.");
	var call = null;
	var hie = null;
	var range = null;
	var lrange = /^L[.](\d+)-(\d+)$/;
	var srange = null;

	// setting replacment causes .subject.description.element. to be replaced.
	var replacement = null;

	if (current != null)
		current.remove();

	if (nid.length > 0 && srcindex[nid] !== undefined)
	{
		range = srcindex[nid];
	}
	else if (lrange.test(nid))
	{
		match = lrange.exec(nid)
		srange = [Number(match[1]), Number(match[2])];
		range = [1, source.length, ""];
	}

	if (range != null)
	{
		if (window.source_code_display != range)
		{
			var start = Math.max(1, range[0]-source_context_quantity);
			var stop = Math.min(source.length, range[1]+source_context_quantity);
			var untraversed = range[2];
			srange = range;

			var lines = source.slice(start-1, stop);
			var text = document.createTextNode(lines.join("\n"));
			var code = document.createElement("code");
			pre = document.createElement("pre");

			var linerange = document.createElement("div");
			var container = document.createElement("div");
			var subcontainer = document.createElement("div");
			var e;

			var lc = range[1] - range[0];

			linerange.appendChild(
				document.createTextNode(
					String(lc) +
					" lines " + String(range[0]) +
					"-" + String(range[1]-1) +
					" from "
				)
			);
			container.appendChild(linerange);
			e = document.createElement("span");
			e.setAttribute("class", "source.file");
			e.appendChild(document.createTextNode(""));
			container.appendChild(e);

			subcontainer.setAttribute("class", "source.code");
			pre.setAttribute("id", "source.code.");

			pre.setAttribute("data-start", String(start));
			code.setAttribute("data-start", String(start));

			offset = start-1;
			pre.setAttribute("data-line-offset", String(offset));
			code.setAttribute("data-line-offset", String(offset));

			untraversed = untraversed.split(' ').join(',')
			pre.setAttribute("data-line", String(untraversed));
			code.setAttribute("data-line", String(untraversed));

			pre.setAttribute("class", " language-python");
			code.setAttribute("class", " language-python");

			container.appendChild(subcontainer);
			subcontainer.appendChild(pre);
			pre.appendChild(code);
			code.appendChild(text);

			hie = code;
			replacement = container;
			// update the current displayed range
			source_code_display = range;
		}
	}
	else
	{
		var ndefault = document.getElementById("subject.default.");
		replacement = ndefault.cloneNode(true);
		hie = null; // no need to highlight subject.default.
	}

	if (replacement != null)
	{
		replacement.setAttribute("id", "subject.description.element.");
		description.appendChild(replacement);
		description.scrollTop = 0;
		description.scrollLeft = 0;
	}

	if (hie != null)
	{
		// prism needs the element to be in the document
		// so highlighting is performed after it's been added

		highlight(hie);
		//Prism.highlightAll();
	}
}

function
init(element)
{
	window.onload = hashchanged;
	Array.prototype.slice.call(document.getElementsByClassName("line.count")).map(
		function(e){e.setAttribute('title', "Line Count")}
	);
	hashchanged(element);
}

window.onload = init;
window.onhashchange = hashchanged;
