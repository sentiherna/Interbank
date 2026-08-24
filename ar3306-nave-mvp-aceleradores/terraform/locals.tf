locals {
  tags = {
    owner     = var.owner
    project   = var.project
    createdBy = var.created_by
    team      = var.team
    deadline  = var.deadline
  }
}
