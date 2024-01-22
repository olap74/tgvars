variable "string1" {
  type = string
}

variable "string2" {
  type = string
}

variable "list1" {
  type = list(string)
}

variable "list2" {
  type = list(string)
}

output "string1" {
  value = var.string1
}

output "string2" {
  value = var.string2
}

output "list1" {
  value = var.list1
}

output "list2" {
  value = var.list2
}
