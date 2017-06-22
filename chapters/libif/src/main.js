/*
	# Browser application for managing source display and external references.
*/
var IS_INNER_FRAME = window.top != window;

var char_page_icon = String.fromCodePoint(128196);
var char_red_x = String.fromCharCode(0x274C);
var char_shrink = String.fromCodePoint(0x1F536);
var char_world = String.fromCodePoint(0x1F30F);
var applications = {};

/*
	# Navigate outward from the element looking for an element
	# with an (xml/attribute)`href`. &null if no ancestor
	# has the attribute.
*/
function
identify_clicked_anchor(element)
{
	while (element && !element.getAttribute("href"))
	{
		if (element == null)
			break;

		element = element.parentElement;
	}

	return element;
}

/*
	# Spawn an application.
	# Currently, only creates an iframe log entry.
*/
function
spawn(link, href)
{
	var log = document.getElementById("log.");
	var container = document.createElement("div");
	var subcontainer = document.createElement("iframe");

	var physical = document.createElement("div");
	var path = document.createElement("span");
	var title = link.getElementsByClassName("identifier")[0];

	{
		var icon = document.createElement("div");
		icon.setAttribute("class", "icon");
		icon.appendChild(document.createTextNode(char_page_icon));
		container.appendChild(icon);
	}

	{
		var actions = document.createElement("div");
		var close = document.createElement("span");
		var shrink = document.createElement("span");

		shrink.setAttribute("class", "shrink");
		close.setAttribute("class", "close");
		actions.setAttribute("class", "log..actions");

		actions.appendChild(shrink);
		actions.appendChild(close);
		close.appendChild(document.createTextNode(char_red_x));
		shrink.appendChild(document.createTextNode(char_shrink));

		close.onclick = destroy_entry;
		shrink.onclick = shrink_entry;
		container.appendChild(actions);
	}

	if (title != null)
	{
		var tid = title.cloneNode(true);
		var t = document.createElement("div");

		t.setAttribute("class", "title");
		t.appendChild(tid);
		container.appendChild(t);
	}

	physical.setAttribute("class", "fragment.address");
	path.setAttribute("class", "url");
	path.appendChild(document.createTextNode(href));

	physical.appendChild(path);
	container.appendChild(physical);

	subcontainer.setAttribute("class", "link");
	subcontainer.setAttribute("src", href);
	container.appendChild(subcontainer);

	cid = "123432123"
	existing = document.getElementById(cid);
	if (existing != null)
	{
		existing.parentNode.removeChild(existing);
		delete applications[cid];
	}

	if (false)
		container.setAttribute("id", cid);

	applications[cid] = null;
	container.setAttribute("class", "new");
	log.insertBefore(container, log.firstChild);
	log.scrollTop = 0;
	log.scrollLeft = 0;

	container.setAttribute("class", "entry");
}

function
activate_link(event)
{
	/*
		# Not desirable. This actually wants to hook
		# into the default handler rather than implement a variant.
	*/
	var pattern = /^https?:.*$/;
	var element = identify_clicked_anchor(event.target);
	if (!element)
		return(true);

	var href = element.getAttribute("href");
	var absolute = pattern.test(href);
	var modifier = event.getModifierState("Shift");

	if ((absolute && !modifier) || (modifier && !absolute))
	{
		event.stopPropagation();
		event.preventDefault();
		spawn(element, element.href);
		return(false);
	}
	else if (href)
	{
		window.location = href;
		event.stopPropagation();
		event.preventDefault();
		return(false);
	}

	return(true);
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

/*
	# Current source code display state.
*/
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
destroy(event)
{
	var element = event.target;
	element.parentNode.removeChild(element);
}

function
set_annihilation(element)
{
	var style = element.getAttribute("style");
	if (style == null)
		style = "";

	style += [
		"transition-duration: 250ms",
		"transition-property: opacity",
		"transition-timing-function: linear",
		"opacity: 0",
	].join(";");

	element.addEventListener("transitionend", destroy, true);
	element.setAttribute("style", style);
}

function
destroy_entry(event)
{
	set_annihilation(event.target.parentNode.parentNode);
}

function
shrink_entry(event)
{
	/*
		# Not implemented.
	*/
}

/**
	# Make an array of elements that contain links to each point
	# in the given xml:id, &xid.

	# [ Parameters ]
	# /xid
		# The XML identifier of the target fragment or subfragment.
**/
function
mkpath(document, xid)
{
	var parts = xid.split(".")
	var curlink = "";
	var elements = Array();

	for (var i in parts)
	{
		var cur = parts[i];
		var sep = document.createElement("span");
		sep.setAttribute("class", "separator");
		sep.appendChild(document.createTextNode("."));

		if (curlink == "")
			curlink = cur;
		else
			curlink = curlink + "." + cur;

		idspan = document.createElement("span");
		linke = document.createElement("a");
		linke.setAttribute("href", "#" + curlink);
		linke.appendChild(document.createTextNode(cur));
		idspan.setAttribute("class", "identifier");
		idspan.appendChild(linke);

		elements.push(idspan);
		elements.push(sep);
	}

	/* remove last separator */
	elements.pop();

	return elements;
}

function
hashchanged()
{
	var nid = window.location.hash.slice(1);
	var log = document.getElementById("log.");
	var factor = document.getElementsByClassName("factor")[0];
	var factor_title = factor.getElementsByClassName("title")[0];
	var hie = null;
	var range = null;
	var lrange = /^L[.](\d+)-(\d+)$/;
	var srange = null;

	if (nid.length > 0 && srcindex[nid] !== undefined)
	{
		range = srcindex[nid];
	}
	else if (lrange.test(nid))
	{
		/*
			# Line range request.
		*/
		match = lrange.exec(nid);
		srange = [Number(match[1]), Number(match[2])];
		range = [1, source.length, String(srange[0]) + "-" + String(srange[1])];
	}

	if (range != null)
	{
		var subject = document.getElementById(nid);
		if (subject != null)
			var title = subject.getElementsByClassName("title")[0];
		else
			var title = null;

		var start = Math.max(1, range[0]-source_context_quantity);
		var stop = Math.min(source.length, range[1]+source_context_quantity);
		var untraversed = range[2];

		var lines = source.slice(start-1, stop);
		var text = document.createTextNode(lines.join("\n"));
		var code = document.createElement("code");
		var pre = document.createElement("pre");

		var container = document.createElement("div");
		var subcontainer = document.createElement("div");

		var physical = document.createElement("div");
		var linerange = document.createElement("span");
		var path = document.createElement("span");

		var lc = (range[1]+1) - range[0];

		{
			var icon = document.createElement("div");
			icon.setAttribute("class", "icon");
			icon.appendChild(document.createTextNode(char_page_icon));
			container.appendChild(icon);
		}

		{
			var actions = document.createElement("div");
			var close = document.createElement("span");
			var shrink = document.createElement("span");

			shrink.setAttribute("class", "shrink");
			close.setAttribute("class", "close");
			actions.setAttribute("class", "log..actions");
			actions.appendChild(shrink);
			actions.appendChild(close);
			close.appendChild(document.createTextNode(char_red_x));
			shrink.appendChild(document.createTextNode(char_shrink));

			close.onclick = destroy_entry;
			shrink.onclick = shrink_entry;
			container.appendChild(actions);
		}

		if (title != null)
		{
			/*
				# Titled fragments.
			*/
			var ftf = factor_title.getElementsByClassName("selected-fragment")[0];
			var tid = title.getElementsByClassName("identifier")[0].cloneNode(true);
			var t = document.createElement("div");
			var leading = documented_module.split('.').concat(nid.split('.'));

			leading.pop();
			leading.push('');

			t.setAttribute("class", "title");
			t.appendChild(document.createTextNode(leading.join('.')));
			t.appendChild(tid);

			container.appendChild(t);

			/*
				# Update factor title fragment.
			*/
			while (ftf.firstChild)
			{
				ftf.removeChild(ftf.firstChild);
			}
			mkpath(document, nid).map(function (x) { ftf.appendChild(x); });
		}

		physical.setAttribute("class", "fragment.address");
		path.setAttribute("class", "relative.file.path");
		path.appendChild(document.createTextNode(factor_source));

		linerange.setAttribute("class", "line.range");
		linerange.appendChild(
			document.createTextNode(
				String(range[0]) + "-" + String(range[1]-1)
			)
		);

		physical.appendChild(path);
		physical.appendChild(document.createTextNode(":"));
		physical.appendChild(linerange);
		container.appendChild(physical);

		subcontainer.setAttribute("class", "syntax.");

		pre.setAttribute("data-start", String(start));
		code.setAttribute("data-start", String(start));

		offset = start-1;
		pre.setAttribute("data-line-offset", String(offset));
		code.setAttribute("data-line-offset", String(offset));

		untraversed = untraversed.split(' ').join(',')
		pre.setAttribute("data-line", String(untraversed));
		code.setAttribute("data-line", String(untraversed));

		pre.setAttribute("class", " language-".concat(default_language));
		code.setAttribute("class", " language-".concat(default_language));

		container.appendChild(subcontainer);
		subcontainer.appendChild(pre);
		pre.appendChild(code);
		code.appendChild(text);

		hie = code;

		cid = "log.." + nid;
		existing = document.getElementById(cid);
		if (existing != null)
			existing.parentNode.removeChild(existing);

		container.setAttribute("id", cid);
		container.setAttribute("class", "new");
		log.insertBefore(container, log.firstChild);
		log.scrollTop = 0;
		log.scrollLeft = 0;

		/*
			# Prism needs the element to be in the document
			# so highlighting is performed after it's been added
		*/
		highlight(hie);
		container.setAttribute("class", "entry");
	}
	else
	{
		hie = null;
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

/*
	# Log application redirects.
*/
window.addEventListener("click", activate_link, false);

/*
	# Reveal target source in Log.
*/
window.onhashchange = hashchanged;
