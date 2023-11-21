#include "telework_types.hh"

using std::string;


EmployeeID::EmployeeID(uint64_t upper, uint64_t lower)
: upper {upper}
, lower {lower}
{}

EmployeeID::EmployeeID()
: upper {0}
, lower {0}
{}

EmployeeID::EmployeeID(string const& uuid) {
	if (uuid.length() != 32) {
		throw std::invalid_argument("Invalid EmployeeID");
	}
	string supper = uuid.substr(0, 16);
	string slower = uuid.substr(16, 16);
	lower = strtoul(slower.c_str(), NULL, 16);
	upper = strtoul(supper.c_str(), NULL, 16);
}

string EmployeeID::str() const {
	char result[33];
	sprintf(result, "%.16lx%.16lx", upper, lower);
	return {result};
}

bool EmployeeID::operator==(EmployeeID const& other) const {
	return other.upper == upper && other.lower == lower;
}


string telework_user_t::serialize() const {
	string result = "0|" + 
		firstname + '|' + 
		lastname + '|' + 
		password + '|' +
		employee_id.str() + '|' +
		job_desc + '|' +
		std::to_string(holidays_left);
	if (remainder.size() > 0) {
		result = result + remainder;
	}
	return result;
}