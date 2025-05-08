terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex" 
      version = "~> 0.141.0"
    }
  }
}

resource "yandex_storage_bucket" "this" {
  bucket     = var.bucket_name
  access_key = null
  secret_key = null
  acl        = var.acl
}