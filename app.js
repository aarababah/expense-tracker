let filters = {}

// Get selected values from years
$("#years").on("change", function() {
	filters["years"] = $("#years").select2("val");
	sendFilters(filters)
})

// Get selected values from months
$("#months").on("change", function() {
	filters["months"] = $("#months").select2("val");
	sendFilters(filters)
})

// Get selected values from category
$("#categories").on("change", function(event) {
	filters["categories"] = $("#categories").select2("val");
	sendFilters(filters)
})

const sendFilters = function(filters){
	d3.json("/filters", {
		method: "POST",
		body: JSON.stringify({
			filters: filters
		}),
		headers: {
	        "Content-type": "application/json; charset=UTF-8"
	    }
	}).then(function(data) {
		d3.select("#transactions").text(data.transactions)
		d3.select("#credit_amt .myvalue").text(data.credit_amt)
		d3.select("#cash_amt .myvalue").text(data.cash_amt)
		d3.select("#expenses .myvalue").text(data.expenses)
		d3.select("#income .myvalue").text(data.income)
		d3.select("#savings_rate .myvalue").text(data.savings_rate) 
		iePlot2(data.exp_key, data.exp_val)
		if (data.subcat_key) {
			iePlot3(data.subcat_key, data.subcat_val)
		}
	});
}

const iePlot2 = function(exp_key, exp_val){

	let expenses = {
		x: exp_key,
		y: exp_val,
		type: "bar",
		name: "Expenses",
		marker:{
			color: "#3D9970"
		}
	}

	let layout = {
		title:"Expense Tracker",
		font: {size: 16},
		xaxis: {
			color: "#3D9970"
		},
        yaxis: {
			title: "Dollars"
			
        }
	}
	data = [expenses]
	Plotly.react("mschart", data, layout)
}


const iePlot3 = function(exp_key, exp_val){

	let expenses = {
		x: exp_key,
		y: exp_val,
		type: "bar",
		name: "Expenses",
		marker:{
			color: "#3D9970"
		}
	}

	let layout = {
		title:"Sub Cat Expense Tracker",
		font: {size: 14},
		xaxis: {
			color: "#3D9970"
		},
        yaxis: {
			title: "Dollars"
			
        }
	}
	data = [expenses]
	Plotly.react("subcategories", data, layout)
}


sendFilters(filters);
