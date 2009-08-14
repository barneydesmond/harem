var i;
var tabs = new Array();

function markFile(hash)
{
	var checkbox = 'checkbox_' + hash;
	if(document.getElementById(checkbox).checked)
	{
		document.getElementById('cell_' + hash).style.background = '#56789A';
	}
	else
	{
		document.getElementById('cell_' + hash).style.background = 'transparent';
	}
}

function showOnly(target)
{
        for (x in tabs)
        {
                if(tabs[x] == target)
                        document.getElementById(tabs[x]).style.display = "block";
                else
                        document.getElementById(tabs[x]).style.display = "none";
        }
}

function toggleCbox(boxid)
{
        var bid = 'box' + boxid;
        document.getElementById(bid).checked = !document.getElementById(bid).checked;
}

